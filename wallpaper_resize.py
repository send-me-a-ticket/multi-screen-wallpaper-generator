import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import io
import zipfile
import os

# Standard resolutions
standard_resolutions = {
    "HD (1280x720)": (1280, 720),
    "FHD (1920x1080)": (1920, 1080),
    "QHD (2560x1440)": (2563, 1440),
    "2K (2048x1080)": (2050, 1080),
    "4K (3840x2160)": (3840, 2160),
    "5K (5120x2880)": (5120, 2880),
    "6K (6144x3160)": (6144, 3160),
    "8K (7680x4320)": (7680, 4320),
    "16K (15360x8640)": (15360, 8640)
}

# Validate monitor connectivity
def is_valid_grid(selected):
    always = (2,2)
    if always not in selected:
        return False
    directions = [(-1,0),(1,0),(0,-1),(0,1)]
    visited = set()
    def dfs(pos):
        if pos in visited:
            return
        visited.add(pos)
        for dx, dy in directions:
            new = (pos[0]+dx, pos[1]+dy)
            if new in selected:
                dfs(new)
    dfs(always)
    return visited == selected

# Streamlit UI
st.set_page_config(page_title="Multi-Screen Wallpaper Generator", layout="wide")
st.title("🖥️ Multi-Screen Wallpaper Generator")

uploaded_images = st.file_uploader("Upload Image(s)", type=["png", "jpg", "jpeg", "webp", "heic"], accept_multiple_files=True)

fit_mode = st.selectbox("Image Fit Mode", ["Fill", "Stretch"], index=0)

# Monitor grid layout
st.markdown("### Monitor Layout (3x3)")
enabled_monitors = set()
for row in range(1, 4):
    cols = st.columns(3)
    for col in range(1, 4):
        pos = (row, col)
        default = (pos == (2,2))
        enabled = cols[col-1].checkbox(f"{pos}", value=default, key=f"chk_{pos}")
        if enabled:
            enabled_monitors.add(pos)

if not is_valid_grid(enabled_monitors):
    st.warning("Ensure monitors are connected (adjacent to at least one other enabled screen). (2,2) must be enabled.")
    st.stop()

st.markdown("### Monitor Settings")
monitor_settings = {}
for pos in sorted(enabled_monitors):
    st.subheader(f"Monitor {pos}")
    col1, col2, col3 = st.columns(3)
    with col1:
        use_custom = st.checkbox("Custom?", key=f"custom_{pos}")
    with col2:
        if use_custom:
            width = st.number_input("Width", min_value=1, key=f"w_{pos}")
            height = st.number_input("Height", min_value=1, key=f"h_{pos}")
        else:
            res_label = st.selectbox("Resolution", list(standard_resolutions.keys()), key=f"res_{pos}")
            width, height = standard_resolutions[res_label]
    with col3:
        alignment = st.selectbox("Alignment", ["Top", "Center", "Bottom"], key=f"align_{pos}")
        offset_x = st.number_input("Offset X", value=0, step=1, key=f"ox_{pos}")
        offset_y = st.number_input("Offset Y", value=0, step=1, key=f"oy_{pos}")
    monitor_settings[pos] = {
        "width": width,
        "height": height,
        "align": alignment,
        "offset_x": offset_x,
        "offset_y": offset_y
    }

generate_split = st.checkbox("Generate as split images (one per monitor)?", value=False)

if st.button("Generate Wallpaper ZIP") and uploaded_images:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for uploaded_file in uploaded_images:
            img = Image.open(uploaded_file)
            img = ImageOps.exif_transpose(img).convert("RGB")
            base_name = os.path.splitext(uploaded_file.name)[0]

            rows = [r for r, _ in enabled_monitors]
            cols = [c for _, c in enabled_monitors]
            min_r, max_r = min(rows), max(rows)
            min_c, max_c = min(cols), max(cols)
            row_count = max_r - min_r + 1
            col_count = max_c - min_c + 1

            row_heights = [0]*row_count
            col_widths = [0]*col_count
            pos_to_idx = {}

            for pos in enabled_monitors:
                r_idx = pos[0] - min_r
                c_idx = pos[1] - min_c
                pos_to_idx[pos] = (r_idx, c_idx)
                mon = monitor_settings[pos]
                col_widths[c_idx] = max(col_widths[c_idx], mon['width'])
                row_heights[r_idx] = max(row_heights[r_idx], mon['height'])

            total_w = sum(col_widths)
            total_h = sum(row_heights)

            col_ratios = [w / total_w for w in col_widths]
            row_ratios = [h / total_h for h in row_heights]

            img_w, img_h = img.size
            grid_parts = [[None]*col_count for _ in range(row_count)]
            x_start = 0
            for c in range(col_count):
                y_start = 0
                crop_w = int(col_ratios[c] * img_w)
                for r in range(row_count):
                    crop_h = int(row_ratios[r] * img_h)
                    if (r+min_r, c+min_c) in enabled_monitors:
                        box = (x_start, y_start, x_start+crop_w, y_start+crop_h)
                        part = img.crop(box)
                        grid_parts[r][c] = part
                    y_start += crop_h
                x_start += crop_w

            final_parts = [[None]*col_count for _ in range(row_count)]
            for r in range(row_count):
                for c in range(col_count):
                    mon_pos = (r+min_r, c+min_c)
                    if mon_pos in enabled_monitors:
                        mon = monitor_settings[mon_pos]
                        part = grid_parts[r][c]

                        # Resize based on fit mode
                        if fit_mode == "Stretch":
                            resized = part.resize((mon['width'], mon['height']), Image.LANCZOS)
                        else:
                            resized = ImageOps.fit(part, (mon['width'], mon['height']), Image.LANCZOS, centering=(0.5, 0.5))

                        final_img = Image.new("RGB", (mon['width'], mon['height']), color=(0,0,0))
                        y_off = 0
                        if mon['align'].lower() == "center":
                            y_off = (mon['height'] - resized.height) // 2
                        elif mon['align'].lower() == "bottom":
                            y_off = mon['height'] - resized.height
                        y_off += mon['offset_y']
                        x_off = mon['offset_x']

                        final_img.paste(resized, (x_off, y_off))
                        final_parts[r][c] = final_img

            if generate_split:
                for r in range(row_count):
                    for c in range(col_count):
                        if final_parts[r][c]:
                            out_img = io.BytesIO()
                            mon_pos = (r+min_r, c+min_c)
                            final_parts[r][c].save(out_img, format="JPEG", quality=95)
                            zipf.writestr(f"{base_name}_{mon_pos[0]}_{mon_pos[1]}.jpg", out_img.getvalue())
            else:
                canvas = Image.new("RGB", (total_w, total_h))
                y = 0
                for r in range(row_count):
                    x = 0
                    for c in range(col_count):
                        if final_parts[r][c]:
                            canvas.paste(final_parts[r][c], (x, y))
                        x += col_widths[c]
                    y += row_heights[r]
                out_img = io.BytesIO()
                canvas.save(out_img, format="JPEG", quality=95)
                zipf.writestr(f"{base_name}_combined.jpg", out_img.getvalue())

    st.download_button("📁 Download ZIP", data=zip_buffer.getvalue(), file_name="wallpapers.zip", mime="application/zip")


hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)