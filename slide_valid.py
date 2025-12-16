import cv2
import ddddocr

from ultralytics import YOLO


def vis_piece(loc, background, slider):
    img_ground = cv2.imread(background)
    img_slider = cv2.imread(slider)
    height, width = img_slider.shape[0:2]
    img = cv2.rectangle(img_ground, (loc, 0, loc + width, height), (0, 0, 0), 1)
    cv2.imshow("a", img)
    cv2.waitKey(0)


# 基于边缘检测
# slider = open("slider.png", "rb").read()
# background = open("background.png", "rb").read()
# slide = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
# res = slide.slide_match(slider, background, simple_target=False)
# loc = res["target"][0]
# vis_piece(loc, "background.png", "slider.png")

# 基于目标检测
model = YOLO("best.pt")  # load a custom model
results = model.predict("background.png")
x = int(results[0].boxes.xyxy[0][0])
loc = x
vis_piece(loc, "background.png", "slider.png")
