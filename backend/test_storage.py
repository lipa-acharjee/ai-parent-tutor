from app.services.storage import storage


test_content = b"Hello from AI Parent Tutor!"

storage.put(
    key="tests/hello.txt",
    body=test_content,
    content_type="text/plain",
)

print("Upload successful!")
print("Key: tests/hello.txt")