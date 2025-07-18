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
    "QHD (2560x1440)": (2560, 1440),
    "2K (2048x1080)": (2048, 1080),
    "4K (3840x2160)": (3840, 2160),
    "5K (5120x2880)": (5120, 2880),
    "6K (6144x3160)": (6144, 3160),
    "8K (7680x4320)": (7680, 4320),
    "16K (15360x8640)": (15360, 8640)
}

# Common monitor sizes in inches
monitor_sizes = {
    "Default": "default",
    "21.5\"": 21.5,
    "24\"": 24,
    "27\"": 27,
    "32\"": 32,
    "34\"": 34,
    "43\"": 43,
    "49\"": 49,
    "Custom": "custom"
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

def calculate_physical_dimensions(width, height, size_inches):
    """Calculate physical dimensions in inches for a given resolution and screen size"""
    if size_inches == "default":
        # Return arbitrary physical dimensions for default case
        return 24.0, 13.5  # Assuming 16:9 aspect ratio at 24" equivalent
    
    # Calculate diagonal in pixels
    diagonal_pixels = (width**2 + height**2)**0.5
    
    # Calculate PPI (pixels per inch)
    ppi = diagonal_pixels / size_inches
    
    # Calculate physical dimensions in inches
    physical_width = width / ppi
    physical_height = height / ppi
    
    return physical_width, physical_height

# Streamlit UI
st.set_page_config(page_title="Multi-Screen Wallpaper Generator", layout="wide")
st.title("🖥️ Multi-Screen Wallpaper Generator")

uploaded_images = st.file_uploader("Upload Image(s)", type=["png", "jpg", "jpeg", "webp", "heic"], accept_multiple_files=True)

fit_mode = st.selectbox("Image Fit Mode", ["Fill", "Stretch"], index=0)

# Global alignment - only show if Fill mode is selected
global_alignment = None
if fit_mode == "Fill":
    global_alignment = st.selectbox(
        "Global Alignment", 
        ["Center", "Top", "Bottom", "Left", "Right", "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"],
        index=0,
        help="Choose which part of the image to focus on when cropping"
    )

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

# Check if any monitor has non-default size
has_custom_sizes = False
for pos in sorted(enabled_monitors):
    if f"size_{pos}" in st.session_state:
        if st.session_state[f"size_{pos}"] != "Default":
            has_custom_sizes = True
            break

for pos in sorted(enabled_monitors):
    st.subheader(f"Monitor {pos}")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        use_custom = st.checkbox("Custom Resolution?", key=f"custom_{pos}")
    
    with col2:
        if use_custom:
            width = st.number_input("Width", min_value=1, key=f"w_{pos}")
            height = st.number_input("Height", min_value=1, key=f"h_{pos}")
        else:
            res_label = st.selectbox("Resolution", list(standard_resolutions.keys()), key=f"res_{pos}")
            width, height = standard_resolutions[res_label]
    
    with col3:
        # Monitor size selection with styling for required input
        size_options = list(monitor_sizes.keys())
        size_key = f"size_{pos}"
        
        # Add styling if custom sizes are being used
        if has_custom_sizes:
            st.markdown("""
            <style>
            .size-required {
                border: 2px solid #ff6b6b !important;
                border-radius: 4px;
            }
            </style>
            """, unsafe_allow_html=True)
            
        size_label = st.selectbox(
            "Monitor Size", 
            size_options, 
            key=size_key,
            help="Select monitor size. Required when any monitor has custom size."
        )
        
        # Handle custom size input
        if size_label == "Custom":
            custom_size = st.number_input(
                "Size (inches)", 
                min_value=10.0, 
                max_value=100.0, 
                value=24.0, 
                step=0.1,
                key=f"custom_size_{pos}"
            )
            size_value = custom_size
        else:
            size_value = monitor_sizes[size_label]
    
    with col4:
        alignment = st.selectbox("Monitor Alignment", ["Top", "Center", "Bottom"], key=f"align_{pos}")
        offset_x = st.number_input("Offset X (viewport shift)", value=0, step=1, key=f"ox_{pos}")
        offset_y = st.number_input("Offset Y (viewport shift)", value=0, step=1, key=f"oy_{pos}")
    
    # Calculate physical dimensions
    physical_width, physical_height = calculate_physical_dimensions(width, height, size_value)
    
    monitor_settings[pos] = {
        "width": width,
        "height": height,
        "physical_width": physical_width,
        "physical_height": physical_height,
        "align": alignment,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "size": size_value
    }

# Warning if sizes are inconsistent
if has_custom_sizes:
    default_count = sum(1 for pos in enabled_monitors if monitor_settings[pos]["size"] == "default")
    if default_count > 0:
        st.warning(f"⚠️ {default_count} monitor(s) still using 'Default' size. Please specify sizes for all monitors when using custom sizes.")

# Display physical dimensions info
st.markdown("### Physical Setup Preview")
with st.expander("View Physical Monitor Dimensions"):
    for pos in sorted(enabled_monitors):
        mon = monitor_settings[pos]
        st.write(f"Monitor {pos}: {mon['width']}x{mon['height']} pixels, {mon['physical_width']:.1f}\"×{mon['physical_height']:.1f}\" physical")

generate_split = st.checkbox("Generate as split images (one per monitor)?", value=False)

def get_global_alignment_centering(alignment):
    """Convert global alignment to centering tuple for ImageOps.fit"""
    alignment_map = {
        "Center": (0.5, 0.5),
        "Top": (0.5, 0.0),
        "Bottom": (0.5, 1.0),
        "Left": (0.0, 0.5),
        "Right": (1.0, 0.5),
        "Top-Left": (0.0, 0.0),
        "Top-Right": (1.0, 0.0),
        "Bottom-Left": (0.0, 1.0),
        "Bottom-Right": (1.0, 1.0)
    }
    return alignment_map.get(alignment, (0.5, 0.5))

if st.button("Generate Wallpaper ZIP") and uploaded_images:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for uploaded_file in uploaded_images:
            img = Image.open(uploaded_file)
            img = ImageOps.exif_transpose(img).convert("RGB")
            base_name = os.path.splitext(uploaded_file.name)[0]

            # Calculate grid dimensions
            rows = [r for r, _ in enabled_monitors]
            cols = [c for _, c in enabled_monitors]
            min_r, max_r = min(rows), max(rows)
            min_c, max_c = min(cols), max(cols)
            row_count = max_r - min_r + 1
            col_count = max_c - min_c + 1

            # Calculate grid layout using PHYSICAL dimensions for proportional content
            # But use PIXEL dimensions for the actual canvas
            col_physical_widths = [0] * col_count
            row_physical_heights = [0] * row_count
            col_pixel_widths = [0] * col_count
            row_pixel_heights = [0] * row_count
            
            for pos in enabled_monitors:
                r_idx = pos[0] - min_r
                c_idx = pos[1] - min_c
                mon = monitor_settings[pos]
                
                # Track both physical and pixel dimensions
                col_physical_widths[c_idx] = max(col_physical_widths[c_idx], mon['physical_width'])
                row_physical_heights[r_idx] = max(row_physical_heights[r_idx], mon['physical_height'])
                col_pixel_widths[c_idx] = max(col_pixel_widths[c_idx], mon['width'])
                row_pixel_heights[r_idx] = max(row_pixel_heights[r_idx], mon['height'])

            # Calculate totals
            total_physical_w = sum(col_physical_widths)
            total_physical_h = sum(row_physical_heights)
            total_pixel_w = sum(col_pixel_widths)
            total_pixel_h = sum(row_pixel_heights)

            # Calculate proportional sections based on PHYSICAL dimensions
            img_w, img_h = img.size
            col_physical_ratios = [w / total_physical_w for w in col_physical_widths]
            row_physical_ratios = [h / total_physical_h for h in row_physical_heights]

            # Extract and process each monitor's portion
            final_parts = {}
            
            for pos in enabled_monitors:
                r_idx = pos[0] - min_r
                c_idx = pos[1] - min_c
                mon = monitor_settings[pos]
                
                # Calculate this monitor's section of the source image based on PHYSICAL proportions
                section_x_start = sum(col_physical_ratios[:c_idx])
                section_y_start = sum(row_physical_ratios[:r_idx])
                section_x_end = section_x_start + col_physical_ratios[c_idx]
                section_y_end = section_y_start + row_physical_ratios[r_idx]
                
                # Convert to pixel coordinates on source image
                crop_left = int(section_x_start * img_w)
                crop_top = int(section_y_start * img_h)
                crop_right = int(section_x_end * img_w)
                crop_bottom = int(section_y_end * img_h)
                
                # Apply viewport offset to the crop coordinates
                offset_x_px = int(mon['offset_x'] * img_w / total_physical_w)
                offset_y_px = int(mon['offset_y'] * img_h / total_physical_h)
                
                crop_left = max(0, min(img_w - 1, crop_left - offset_x_px))
                crop_right = max(crop_left + 1, min(img_w, crop_right - offset_x_px))
                crop_top = max(0, min(img_h - 1, crop_top - offset_y_px))
                crop_bottom = max(crop_top + 1, min(img_h, crop_bottom - offset_y_px))
                
                # Crop the section
                section = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                
                # Resize to the monitor's PIXEL resolution
                if fit_mode == "Stretch":
                    # Stretch to exact monitor resolution
                    final_img = section.resize((mon['width'], mon['height']), Image.LANCZOS)
                    
                else:  # Fill mode
                    # Fill the entire monitor area, cropping as needed
                    centering = get_global_alignment_centering(global_alignment)
                    final_img = ImageOps.fit(section, (mon['width'], mon['height']), Image.LANCZOS, centering=centering)
                
                final_parts[pos] = final_img

            # Generate output based on split mode
            if generate_split:
                # Save individual monitor images
                for pos in enabled_monitors:
                    if pos in final_parts:
                        out_img = io.BytesIO()
                        final_parts[pos].save(out_img, format="JPEG", quality=95)
                        zipf.writestr(f"{base_name}_{pos[0]}_{pos[1]}.jpg", out_img.getvalue())
            else:
                # Create combined canvas using PIXEL dimensions
                canvas = Image.new("RGB", (total_pixel_w, total_pixel_h), color=(0, 0, 0))
                
                # Place each monitor image on the canvas
                for pos in enabled_monitors:
                    if pos in final_parts:
                        r_idx = pos[0] - min_r
                        c_idx = pos[1] - min_c
                        
                        canvas_x = sum(col_pixel_widths[:c_idx])
                        canvas_y = sum(row_pixel_heights[:r_idx])
                        
                        # Calculate position based on monitor alignment within the grid cell
                        cell_width = col_pixel_widths[c_idx]
                        cell_height = row_pixel_heights[r_idx]
                        img_width = final_parts[pos].width
                        img_height = final_parts[pos].height
                        
                        # Center horizontally within the cell
                        offset_x = (cell_width - img_width) // 2
                        
                        # Apply vertical alignment
                        if monitor_settings[pos]['align'].lower() == "center":
                            offset_y = (cell_height - img_height) // 2
                        elif monitor_settings[pos]['align'].lower() == "bottom":
                            offset_y = cell_height - img_height
                        else:  # top
                            offset_y = 0
                        
                        canvas.paste(final_parts[pos], (canvas_x + offset_x, canvas_y + offset_y))
                
                # Save combined image
                out_img = io.BytesIO()
                canvas.save(out_img, format="JPEG", quality=95)
                zipf.writestr(f"{base_name}_combined.jpg", out_img.getvalue())

    st.download_button("📁 Download ZIP", data=zip_buffer.getvalue(), file_name="wallpapers.zip", mime="application/zip")

# Add author notes
st.markdown("""
### Created by Gaurav Poudel (@send_me_a_ticket)
""")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
