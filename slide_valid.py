import cv2
import ddddocr

# slider_gray = cv2.imread("background.png", 0)
slider = open("slider.png", "rb").read()
background = open("background.png", "rb").read()
slide = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
res = slide.slide_match(slider, background, simple_target=False)

print(res)
print(res["target"][0])

# bg_edge = cv2.Canny(background_gray, 100, 200,apertureSize=3)
# tp_edge = cv2.Canny(slider_gray, 100, 200 ,apertureSize=3)

# result = cv2.matchTemplate(bg_edge, tp_edge, cv2.TM_CCOEFF_NORMED)
# min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
#
# print(max_loc[0])
#
slider_gray = cv2.imread("slider.png")
print(slider_gray.shape[0:2])
height, width = slider_gray.shape[0:2]
background = cv2.imread("background.png")
img = cv2.rectangle(background,
                    (res["target"][0], int(0)), (int(res["target"][0] + width), int(0 + height)), (0, 0, 0),
                    1)
cv2.imshow("a", img)
cv2.waitKey(0)
