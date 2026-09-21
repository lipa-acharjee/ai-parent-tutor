import asyncio
import hashlib
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from textwrap import wrap

import edge_tts
from PIL import Image, ImageDraw, ImageFont

from app.services.video.interface import VideoProvider
from app.services.video.models import VideoRequest, VideoResult


class LocalVideoProvider(VideoProvider):

    def __init__(self):
        self.base_dir = Path("/tmp/video")

        self.default_voice = "en-US-JennyNeural"

        self.width = 1280
        self.height = 720
        self.fps = 30

        self.base_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def name(self) -> str:
        return "local"

    async def generate(
        self,
        request: VideoRequest,
    ) -> VideoResult:

        job_id = str(uuid.uuid4())

        output_dir = self.base_dir / job_id
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:

            self._check_ffmpeg()

            scene_list = self._build_scene_list(
                request
            )

            if not scene_list:
                raise ValueError(
                    "Lesson does not contain any video scenes."
                )

            segment_paths = []

            total_scenes = len(scene_list)

            for index, scene in enumerate(
                scene_list,
                start=1,
            ):

                scene_dir = (
                    output_dir
                    / f"scene_{index:03d}"
                )

                scene_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                narration = scene.get(
                    "narration",
                    "",
                ).strip()

                if not narration:
                    narration = scene.get(
                        "title",
                        "Lesson scene",
                    )

                audio_path = (
                    scene_dir
                    / "narration.mp3"
                )

                image_path = (
                    scene_dir
                    / "visual.png"
                )

                segment_path = (
                    scene_dir
                    / "segment.mp4"
                )

                await self._generate_audio(
                    text=narration,
                    output_path=audio_path,
                    voice=request.voice,
                )

                self._generate_educational_visual(
                    title=scene.get(
                        "title",
                        "Lesson",
                    ),
                    narration=narration,
                    visual_description=scene.get(
                        "visual_description",
                        "",
                    ),
                    output_path=image_path,
                    scene_number=index,
                    total_scenes=total_scenes,
                )

                self._compose_segment(
                    image_path=image_path,
                    audio_path=audio_path,
                    output_path=segment_path,
                )

                segment_paths.append(
                    segment_path
                )

            final_path = (
                output_dir
                / "lesson.mp4"
            )

            self._combine_segments(
                segment_paths=segment_paths,
                output_path=final_path,
            )

            return VideoResult(
                success=True,
                provider=self.name,
                local_path=str(final_path),
                job_id=job_id,
                status="completed",
            )

        except Exception as exc:

            return VideoResult(
                success=False,
                provider=self.name,
                job_id=job_id,
                status="failed",
                error=str(exc),
            )

    async def get_status(
        self,
        job_id: str,
    ) -> VideoResult:

        output_dir = self.base_dir / job_id
        final_path = output_dir / "lesson.mp4"

        if final_path.exists():

            return VideoResult(
                success=True,
                provider=self.name,
                job_id=job_id,
                local_path=str(final_path),
                status="completed",
            )

        if output_dir.exists():

            return VideoResult(
                success=True,
                provider=self.name,
                job_id=job_id,
                status="processing",
            )

        return VideoResult(
            success=False,
            provider=self.name,
            job_id=job_id,
            status="failed",
            error="Video job was not found.",
        )

    async def cancel(
        self,
        job_id: str,
    ) -> bool:

        output_dir = self.base_dir / job_id

        if output_dir.exists():
            shutil.rmtree(
                output_dir,
                ignore_errors=True,
            )

        return True

    # =========================================================
    # Scene preparation
    # =========================================================

    def _build_scene_list(
        self,
        request: VideoRequest,
    ):

        scenes = []

        script = request.script

        if script.introduction.strip():

            scenes.append(
                {
                    "title": "Introduction",
                    "narration": script.introduction,
                    "visual_description": (
                        f"Introduce the lesson topic: "
                        f"{script.title}"
                    ),
                    "duration_seconds": 20,
                }
            )

        for scene in script.scenes:

            scenes.append(
                {
                    "title": scene.title,
                    "narration": scene.narration,
                    "visual_description": (
                        scene.visual_description
                        or scene.title
                    ),
                    "duration_seconds": (
                        scene.duration_seconds
                        or 30
                    ),
                }
            )

        if script.conclusion.strip():

            scenes.append(
                {
                    "title": "Conclusion",
                    "narration": script.conclusion,
                    "visual_description": (
                        "Summary of the important "
                        "ideas learned in this lesson"
                    ),
                    "duration_seconds": 20,
                }
            )

        return scenes

    # =========================================================
    # Educational visual generation
    # =========================================================

    def _generate_educational_visual(
        self,
        title: str,
        narration: str,
        visual_description: str,
        output_path: Path,
        scene_number: int,
        total_scenes: int,
    ):

        image = Image.new(
            "RGB",
            (
                self.width,
                self.height,
            ),
            "white",
        )

        draw = ImageDraw.Draw(image)

        title_font = self._font(42)
        subtitle_font = self._font(28)
        body_font = self._font(25)
        small_font = self._font(21)

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        draw.rectangle(
            (
                0,
                0,
                self.width,
                105,
            ),
            fill=(245, 245, 245),
            outline=(30, 30, 30),
            width=2,
        )

        self._draw_centered_text(
            draw,
            title,
            y=25,
            font=title_font,
            max_width=1120,
        )

        # -----------------------------------------------------
        # Scene indicator
        # -----------------------------------------------------

        scene_text = (
            f"Scene {scene_number} of {total_scenes}"
        )

        draw.text(
            (
                45,
                125,
            ),
            scene_text,
            font=small_font,
            fill=(90, 90, 90),
        )

        # -----------------------------------------------------
        # Main educational visual
        # -----------------------------------------------------

        visual_area = (
            55,
            165,
            1225,
            485,
        )

        self._draw_visual_from_description(
            draw=draw,
            visual_description=visual_description,
            narration=narration,
            area=visual_area,
            title=title,
            body_font=body_font,
            subtitle_font=subtitle_font,
        )

        # -----------------------------------------------------
        # Bottom teaching caption
        # -----------------------------------------------------

        caption_area = (
            55,
            515,
            1225,
            675,
        )

        self._draw_caption(
            draw=draw,
            text=narration,
            area=caption_area,
            font=small_font,
        )

        image.save(
            output_path,
            format="PNG",
        )

    def _draw_visual_from_description(
        self,
        draw,
        visual_description: str,
        narration: str,
        area,
        title,
        body_font,
        subtitle_font,
    ):

        x1, y1, x2, y2 = area

        description = (
            visual_description or ""
        ).lower()

        combined = (
            description
            + " "
            + narration.lower()
            + " "
            + title.lower()
        )

        # -----------------------------------------------------
        # Water states
        # -----------------------------------------------------

        if any(
            word in combined
            for word in [
                "solid",
                "liquid",
                "gas",
                "ice",
                "steam",
                "states of water",
            ]
        ):

            self._draw_water_states(
                draw,
                area,
                subtitle_font,
                body_font,
            )

            return

        # -----------------------------------------------------
        # Plant / photosynthesis-style diagram
        # -----------------------------------------------------

        if any(
            word in combined
            for word in [
                "plant",
                "leaf",
                "leaves",
                "photosynthesis",
                "sunlight",
            ]
        ):

            self._draw_plant_diagram(
                draw,
                area,
                subtitle_font,
                body_font,
            )

            return

        # -----------------------------------------------------
        # Life cycle / process
        # -----------------------------------------------------

        if any(
            word in combined
            for word in [
                "cycle",
                "process",
                "steps",
                "stage",
                "stages",
            ]
        ):

            self._draw_process_diagram(
                draw,
                area,
                subtitle_font,
                body_font,
            )

            return

        # -----------------------------------------------------
        # Food / digestion
        # -----------------------------------------------------

        if any(
            word in combined
            for word in [
                "food",
                "eat",
                "digestion",
                "stomach",
            ]
        ):

            self._draw_simple_process(
                draw,
                area,
                [
                    "Food",
                    "Mouth",
                    "Stomach",
                    "Body",
                ],
                subtitle_font,
            )

            return

        # -----------------------------------------------------
        # Sun / Earth
        # -----------------------------------------------------

        if any(
            word in combined
            for word in [
                "sun",
                "earth",
                "planet",
                "solar",
            ]
        ):

            self._draw_sun_earth(
                draw,
                area,
                subtitle_font,
                body_font,
            )

            return

        # -----------------------------------------------------
        # Generic educational diagram
        # -----------------------------------------------------

        self._draw_generic_visual(
            draw,
            area,
            visual_description,
            narration,
            subtitle_font,
            body_font,
        )

    # =========================================================
    # Visual templates
    # =========================================================

    def _draw_water_states(
        self,
        draw,
        area,
        title_font,
        body_font,
    ):

        x1, y1, x2, y2 = area

        boxes = [
            ("ICE", "SOLID"),
            ("WATER", "LIQUID"),
            ("STEAM", "GAS"),
        ]

        centers = [
            x1 + 200,
            (x1 + x2) // 2,
            x2 - 200,
        ]

        for index, (
            object_name,
            state,
        ) in enumerate(boxes):

            cx = centers[index]

            draw.ellipse(
                (
                    cx - 85,
                    y1 + 80,
                    cx + 85,
                    y1 + 250,
                ),
                outline=(30, 30, 30),
                width=4,
            )

            self._draw_centered_text(
                draw,
                object_name,
                y=y1 + 135,
                font=title_font,
                center_x=cx,
            )

            self._draw_centered_text(
                draw,
                state,
                y=y1 + 290,
                font=body_font,
                center_x=cx,
            )

        self._arrow(
            draw,
            centers[0] + 100,
            y1 + 165,
            centers[1] - 100,
            y1 + 165,
        )

        self._arrow(
            draw,
            centers[1] + 100,
            y1 + 165,
            centers[2] - 100,
            y1 + 165,
        )

        self._draw_centered_text(
            draw,
            "Water can change from one state to another.",
            y=y1 + 365,
            font=body_font,
            center_x=(x1 + x2) // 2,
            max_width=x2 - x1 - 100,
        )

    def _draw_plant_diagram(
        self,
        draw,
        area,
        title_font,
        body_font,
    ):

        x1, y1, x2, y2 = area

        sun_x = x1 + 190
        sun_y = y1 + 120

        draw.ellipse(
            (
                sun_x - 65,
                sun_y - 65,
                sun_x + 65,
                sun_y + 65,
            ),
            outline=(30, 30, 30),
            width=5,
        )

        self._draw_centered_text(
            draw,
            "SUN",
            y=sun_y - 15,
            font=body_font,
            center_x=sun_x,
        )

        plant_x = (x1 + x2) // 2

        draw.line(
            (
                plant_x,
                y1 + 400,
                plant_x,
                y1 + 150,
            ),
            fill=(30, 30, 30),
            width=12,
        )

        draw.ellipse(
            (
                plant_x - 130,
                y1 + 185,
                plant_x - 15,
                y1 + 260,
            ),
            outline=(30, 30, 30),
            width=4,
        )

        draw.ellipse(
            (
                plant_x + 15,
                y1 + 225,
                plant_x + 130,
                y1 + 300,
            ),
            outline=(30, 30, 30),
            width=4,
        )

        draw.line(
            (
                plant_x,
                y1 + 400,
                plant_x - 80,
                y1 + 450,
            ),
            fill=(30, 30, 30),
            width=6,
        )

        draw.line(
            (
                plant_x,
                y1 + 400,
                plant_x + 80,
                y1 + 450,
            ),
            fill=(30, 30, 30),
            width=6,
        )

        self._arrow(
            draw,
            sun_x + 75,
            sun_y,
            plant_x - 125,
            y1 + 220,
        )

        self._draw_centered_text(
            draw,
            "Sunlight",
            y=y1 + 25,
            font=body_font,
            center_x=(sun_x + plant_x) // 2,
        )

        self._draw_centered_text(
            draw,
            "PLANT",
            y=y1 + 405,
            font=body_font,
            center_x=plant_x,
        )

    def _draw_process_diagram(
        self,
        draw,
        area,
        title_font,
        body_font,
    ):

        x1, y1, x2, y2 = area

        steps = [
            "START",
            "UNDERSTAND",
            "CHANGE",
            "RESULT",
        ]

        width = 235
        gap = 35

        total = (
            len(steps) * width
            + (len(steps) - 1) * gap
        )

        start_x = (
            x1
            + (x2 - x1 - total) // 2
        )

        y = y1 + 130

        centers = []

        for index, step in enumerate(steps):

            left = (
                start_x
                + index * (width + gap)
            )

            draw.rounded_rectangle(
                (
                    left,
                    y,
                    left + width,
                    y + 130,
                ),
                radius=20,
                outline=(30, 30, 30),
                width=4,
            )

            self._draw_centered_text(
                draw,
                step,
                y=y + 45,
                font=body_font,
                center_x=left + width // 2,
                max_width=width - 25,
            )

            centers.append(
                left + width
            )

        for index in range(
            len(centers) - 1
        ):

            self._arrow(
                draw,
                centers[index] + 5,
                y + 65,
                centers[index] + gap - 5,
                y + 65,
            )

        self._draw_centered_text(
            draw,
            "Learning happens step by step.",
            y=y + 220,
            font=body_font,
            center_x=(x1 + x2) // 2,
        )

    def _draw_simple_process(
        self,
        draw,
        area,
        steps,
        font,
    ):

        x1, y1, x2, y2 = area

        box_width = 210
        box_height = 110
        gap = 45

        total_width = (
            len(steps) * box_width
            + (len(steps) - 1) * gap
        )

        start_x = (
            x1
            + (x2 - x1 - total_width) // 2
        )

        y = y1 + 130

        for index, step in enumerate(steps):

            left = (
                start_x
                + index * (box_width + gap)
            )

            draw.rounded_rectangle(
                (
                    left,
                    y,
                    left + box_width,
                    y + box_height,
                ),
                radius=18,
                outline=(30, 30, 30),
                width=4,
            )

            self._draw_centered_text(
                draw,
                step,
                y=y + 35,
                font=font,
                center_x=left + box_width // 2,
            )

            if index < len(steps) - 1:

                self._arrow(
                    draw,
                    left + box_width + 5,
                    y + box_height // 2,
                    left + box_width + gap - 5,
                    y + box_height // 2,
                )

    def _draw_sun_earth(
        self,
        draw,
        area,
        title_font,
        body_font,
    ):

        x1, y1, x2, y2 = area

        sun_x = x1 + 250
        earth_x = x2 - 250
        center_y = y1 + 220

        draw.ellipse(
            (
                sun_x - 100,
                center_y - 100,
                sun_x + 100,
                center_y + 100,
            ),
            outline=(30, 30, 30),
            width=5,
        )

        self._draw_centered_text(
            draw,
            "SUN",
            y=center_y - 20,
            font=title_font,
            center_x=sun_x,
        )

        draw.ellipse(
            (
                earth_x - 75,
                center_y - 75,
                earth_x + 75,
                center_y + 75,
            ),
            outline=(30, 30, 30),
            width=5,
        )

        self._draw_centered_text(
            draw,
            "EARTH",
            y=center_y - 15,
            font=body_font,
            center_x=earth_x,
        )

        self._arrow(
            draw,
            sun_x + 110,
            center_y,
            earth_x - 110,
            center_y,
        )

        self._draw_centered_text(
            draw,
            "Energy / light",
            y=center_y + 120,
            font=body_font,
            center_x=(sun_x + earth_x) // 2,
        )

    def _draw_generic_visual(
        self,
        draw,
        area,
        visual_description,
        narration,
        title_font,
        body_font,
    ):

        x1, y1, x2, y2 = area

        center_x = (x1 + x2) // 2

        draw.rounded_rectangle(
            (
                x1 + 70,
                y1 + 50,
                x2 - 70,
                y2 - 40,
            ),
            radius=25,
            outline=(30, 30, 30),
            width=4,
        )

        label = self._clean_visual_description(
            visual_description
        )

        lines = self._wrap_text(
            label,
            body_font,
            x2 - x1 - 240,
        )

        current_y = y1 + 115

        for line in lines[:8]:

            self._draw_centered_text(
                draw,
                line,
                y=current_y,
                font=body_font,
                center_x=center_x,
            )

            current_y += 42

        self._draw_centered_text(
            draw,
            "Think about what this picture is teaching you.",
            y=y2 - 100,
            font=title_font,
            center_x=center_x,
            max_width=x2 - x1 - 150,
        )

    # =========================================================
    # Caption
    # =========================================================

    def _draw_caption(
        self,
        draw,
        text,
        area,
        font,
    ):

        x1, y1, x2, y2 = area

        draw.line(
            (
                x1,
                y1,
                x2,
                y1,
            ),
            fill=(150, 150, 150),
            width=2,
        )

        clean_text = self._clean_text(
            text
        )

        lines = self._wrap_text(
            clean_text,
            font,
            x2 - x1 - 40,
        )

        current_y = y1 + 15

        for line in lines[:4]:

            draw.text(
                (
                    x1 + 20,
                    current_y,
                ),
                line,
                font=font,
                fill=(30, 30, 30),
            )

            current_y += 32

    # =========================================================
    # Audio
    # =========================================================

    async def _generate_audio(
        self,
        text: str,
        output_path: Path,
        voice: str | None = None,
    ):

        selected_voice = (
            voice
            or self.default_voice
        )

        communicate = edge_tts.Communicate(
            text=text,
            voice=selected_voice,
        )

        await communicate.save(
            str(output_path)
        )

    # =========================================================
    # FFmpeg
    # =========================================================

    def _compose_segment(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
    ):

        command = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-i",
            str(audio_path),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            "-r",
            str(self.fps),
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        self._run_ffmpeg(command)

    def _combine_segments(
        self,
        segment_paths,
        output_path: Path,
    ):

        concat_file = (
            output_path.parent
            / "concat.txt"
        )

        with open(
            concat_file,
            "w",
            encoding="utf-8",
        ) as f:

            for path in segment_paths:

                safe_path = (
                    str(path)
                    .replace("\\", "/")
                    .replace("'", "'\\''")
                )

                f.write(
                    f"file '{safe_path}'\n"
                )

        command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        self._run_ffmpeg(command)

    def _check_ffmpeg(self):

        if shutil.which("ffmpeg") is None:

            raise RuntimeError(
                "FFmpeg is not installed or "
                "not available in PATH."
            )

    def _run_ffmpeg(
        self,
        command,
    ):

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:

            raise RuntimeError(
                "FFmpeg failed:\n"
                + result.stderr[-4000:]
            )

    # =========================================================
    # Drawing helpers
    # =========================================================

    def _font(self, size: int):

        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

        for candidate in candidates:

            path = Path(candidate)

            if path.exists():

                return ImageFont.truetype(
                    str(path),
                    size,
                )

        return ImageFont.load_default()

    def _draw_centered_text(
        self,
        draw,
        text,
        y,
        font,
        center_x=None,
        max_width=None,
    ):

        if center_x is None:
            center_x = self.width // 2

        if max_width:

            lines = self._wrap_text(
                text,
                font,
                max_width,
            )

        else:

            lines = [text]

        current_y = y

        for line in lines:

            bbox = draw.textbbox(
                (0, 0),
                line,
                font=font,
            )

            text_width = (
                bbox[2] - bbox[0]
            )

            x = (
                center_x
                - text_width // 2
            )

            draw.text(
                (
                    x,
                    current_y,
                ),
                line,
                font=font,
                fill=(30, 30, 30),
            )

            current_y += (
                bbox[3] - bbox[1]
                + 8
            )

    def _wrap_text(
        self,
        text,
        font,
        max_width,
    ):

        words = text.split()

        if not words:
            return []

        lines = []
        current = ""

        for word in words:

            candidate = (
                f"{current} {word}".strip()
            )

            bbox = ImageDraw.Draw(
                Image.new("RGB", (1, 1))
            ).textbbox(
                (0, 0),
                candidate,
                font=font,
            )

            width = (
                bbox[2] - bbox[0]
            )

            if (
                width <= max_width
                or not current
            ):

                current = candidate

            else:

                lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def _arrow(
        self,
        draw,
        x1,
        y1,
        x2,
        y2,
    ):

        draw.line(
            (
                x1,
                y1,
                x2,
                y2,
            ),
            fill=(30, 30, 30),
            width=5,
        )

        arrow_size = 16

        draw.polygon(
            [
                (
                    x2,
                    y2,
                ),
                (
                    x2 - arrow_size,
                    y2 - arrow_size,
                ),
                (
                    x2 - arrow_size,
                    y2 + arrow_size,
                ),
            ],
            fill=(30, 30, 30),
        )

    def _clean_text(
        self,
        text,
    ):

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _clean_visual_description(
        self,
        text,
    ):

        text = self._clean_text(
            text
        )

        text = text.replace(
            "show ",
            "",
        )

        text = text.replace(
            "display ",
            "",
        )

        return text.strip()