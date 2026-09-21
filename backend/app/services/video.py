import asyncio, json, os, subprocess, tempfile
from pathlib import Path

class VideoRenderer:
    """Production adapter boundary. Current renderer creates narrated educational slides.
    Replace generate_voice() / render_visual() with a managed media provider for richer AI video."""
    async def generate_voice(self, text: str, output: str):
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("Install edge-tts to enable narration")
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(output)

    def render_visual(self, scene, output_png):
        from PIL import Image, ImageDraw, ImageFont
        img=Image.new("RGB", (1280,720), "white")
        d=ImageDraw.Draw(img)
        d.text((70,70), scene.get("title", "Learning"), fill="black")
        d.text((70,190), scene.get("visual", "Educational illustration"), fill="black")
        img.save(output_png)

    async def render(self, scenes, output):
        with tempfile.TemporaryDirectory() as td:
            clips=[]
            for i, scene in enumerate(scenes):
                png=os.path.join(td, f"{i}.png"); wav=os.path.join(td, f"{i}.mp3"); mp4=os.path.join(td, f"{i}.mp4")
                scene.setdefault("title", f"Lesson {i+1}")
                self.render_visual(scene,png)
                await self.generate_voice(scene.get("narration", ""), wav)
                seconds=max(3,int(scene.get("seconds",8)))
                subprocess.run(["ffmpeg","-y","-loop","1","-i",png,"-i",wav,"-t",str(seconds),"-vf","scale=1280:720","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-shortest",mp4],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                clips.append(mp4)
            concat=os.path.join(td,"concat.txt")
            Path(concat).write_text("\n".join(f"file '{p}'" for p in clips))
            subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy",output],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

video_renderer=VideoRenderer()
