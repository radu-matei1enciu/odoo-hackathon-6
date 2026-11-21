# Media upload (photos and videos)

Plan for letting a post carry several photos and videos. **Implemented** (steps 1-4 below); step 5 (Pillow) is not.

Decisions taken for the open points in section 5:

- Media-only posts: not allowed, text is still required.
- Limits: 4 files per post (`MAX_FILES` in `board.py`), 50 MB per request (`MAX_CONTENT_LENGTH` in `__init__.py`).
- `minimal`: text links with file size, no thumbnails.
- EXIF: not stripped yet (needs Pillow).

## 1. Data model

A post can have many files, so add an `Attachment` model in `app/db.py` instead of extra columns on `Post`:

```python
class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.ForeignKey("post.id"), nullable=False)
    filename = db.Column(db.String(64), nullable=False)    # name on disk, e.g. uuid4 hex + ".jpg"
    original_name = db.Column(db.String(255))              # what the user uploaded, display only
    kind = db.Column(db.String(10), nullable=False)        # image | video
    mimetype = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Integer, nullable=False)           # bytes, shown in the minimal tier

# on Post:
attachments = db.relationship("Attachment", backref="post", order_by="Attachment.id")
```

This is a model change: run `flask --app app init-db` again (wipes data).

## 2. Storage

- Files go on disk in `instance/uploads/`, not in SQLite. `instance/` is already gitignored, and keeping uploads out of `static/` means nobody can drop files into the app's code tree.
- Name each file `uuid4().hex` plus the extension. Never use the uploaded name on disk (collisions, path traversal). The original name is stored only for display.
- Serve files through a route in `board.py`, `/media/<filename>`, with `send_from_directory`. It goes through `before_request` like the rest of the board, so in `rest` it returns 503 automatically.
- `init-db` also empties `instance/uploads/`, so no files are left behind after the tables are wiped.

## 3. Form and upload handling (no JS needed)

- Post form: add `enctype="multipart/form-data"` and
  `<input type="file" name="media" multiple accept="image/*,video/*">`.
  The browser's own `multiple` handles picking several files, so posting still works in every tier without JS.
- In `create()`: loop over `request.files.getlist("media")`, skip empty entries, save each file and add an `Attachment`, all in the same commit as the post.
- Validation:
  - Allowed extensions and mimetypes only: `jpg/jpeg/png/webp/gif`, `mp4/webm`. No SVG (it can carry scripts).
  - Maximum number of files per post (e.g. 4).
  - `MAX_CONTENT_LENGTH` in config (e.g. 50 MB). Flask rejects larger uploads with 413, which needs a friendly error page.
  - On a validation error: flash a message and redirect, like an empty post today.

## 4. Rendering per tier

Everyone can always get to the media; only how it is shown changes.

| tier      | images                              | videos                                                  |
|-----------|-------------------------------------|---------------------------------------------------------|
| `full`    | inline `<img loading="lazy">`       | `<video controls preload="none">`, nothing downloads until play |
| `minimal` | text link: "photo: garden.jpg (1.2 MB)" | text link: "video: storm.mp4 (14 MB)"               |
| `rest`    | nothing, plain-text 503             | nothing                                                 |

Showing the file size in `minimal` is honest about the energy cost: people decide whether a download is worth it. The template branches on `tier`, as `base.html` already does for JS.

## 5. Open decisions

1. **Media-only posts:** `body` is required today. Allow a photo with no text?
2. **Limits:** files per post and maximum size. Videos are what really cost bandwidth and energy.
3. **What `minimal` shows:** links only (no new dependency) or small image thumbnails. Thumbnails need Pillow to resize at upload time. Video thumbnails would need ffmpeg (skip). Dithering is on the "not building" list.
4. **Privacy, strip EXIF data:** phone photos often contain GPS location. Removing it also needs Pillow (re-saving the image drops the data). Recommended for an anonymous public board if Pillow is added anyway.
5. **Abuse:** no auth, so anyone can fill the disk. For the demo, the limits in point 2 are probably enough.

## 6. Suggested order

1. Model and `init-db` cleanup.
2. Upload handling with validation in `create()`.
3. `/media/<filename>` route.
4. Template rendering per tier.
5. Optional: Pillow for EXIF stripping and thumbnails.

Steps 1-4 need no new dependencies.
