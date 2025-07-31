# Multi Screen Wallpaper Generator
Generates single wallpaper image for multiple screen sizes & resolutions.

For scenarios where you are using multiple monitors of different resolutions, layouts, and sizes, this tool can instantly generate wallpapers that look seamless and beautiful !

Additional features like size control, custom resolution and image processing modes help you find the perfect tune that works for any combination.

## To Use
### Windows Users
Simply download the exe and run. The windows binary is wrapped with python runtime and streamlit. You may provide a blank email on first launch (just press enter).

[Download Here](https://github.com/send-me-a-ticket/multi-screen-wallpaper-generator/releases/tag/pre-release)

### Linux/MacOS Users
Install Python (3.9+). Make sure to install dependencies - numpy, streamlit and pillow:

```pip install numpy streamlit pillow```

```streamlit run wallpaper_resize.py```

## Input Example
Single ultrawide image

![0 (8)](https://github.com/user-attachments/assets/9c48a5fe-d5d0-40e6-80bc-139aa77886f5)


## Output Example
when applied, the below image perfectly spans 3 monitors, where left and right ones are 4k, and center is QHD (see config options below).

![0 (8)_combined](https://github.com/user-attachments/assets/7acbf1be-4e2e-4517-9610-d235eadb550b)

## Application Preview
<img width="918" height="1791" alt="image" src="https://github.com/user-attachments/assets/e6444462-bd88-4b1d-8439-070e86002e9e" />

### Badges
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-orange)
![License](https://img.shields.io/github/license/send-me-a-ticket/multi-screen-wallpaper-generator)
