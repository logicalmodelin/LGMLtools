import cv2
import numpy as np

def main():
    raw_img:np.ndarray = cv2.imread('images/face.png', cv2.IMREAD_GRAYSCALE)
    _,src_img = cv2.threshold(raw_img, 0, 255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    height: int
    width: int
    height, width = raw_img.shape[:2]
    contours: np.ndarray  # points of contours
    hierarchy: np.ndarray
    contours, hierarchy = cv2.findContours(src_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html#gadf1ad6a0b82947fa1fe3c3d497f260e0
    """
    [hierarchy]
    Optional output vector (e.g. std::vector<cv::Vec4i>), 
    containing information about the image topology. It has as many elements as the number of contours. 
    For each i-th contour contours[i], 
     - In Python, hierarchy is nested inside a top level array. 
     - Use hierarchy[0][i] to access hierarchical elements of i-th contour.
    the elements hierarchy[i][0] , hierarchy[i][1] , hierarchy[i][2] , and hierarchy[i][3] are 
    set to 0-based indices in contours of the next and previous contours at the same hierarchical level,
    the first child contour and the parent contour, respectively.
    If for the contour i there are no next, previous, parent, or nested contours,
    the corresponding elements of hierarchy[i] will be negative.
    [[次の兄弟、前の兄弟、子供、親], [繰り返し], [繰り返し]...]
    """
    dist_img: np.ndarray = np.empty(src_img.shape, dtype=np.float32)
    for c in contours:
        print(c.shape)

    target_index: int = 0
    for i in range(src_img.shape[0]):
        for j in range(src_img.shape[1]):
            # https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html#ga1a539e8db2135af2566103705d7a5722
            # 正値（内側），負置（外側）, 0（辺上）
            dist_img[i,j] = cv2.pointPolygonTest(contours[target_index], (j,i), True)
    min_val: float
    max_val: float
    min_loc: tuple[int, int]
    max_loc: tuple[int, int]
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(dist_img)
    min_val = abs(min_val)
    max_val = abs(max_val)

    dw_img: np.ndarray = np.zeros((height, width, 3), dtype=np.uint8)
    v: int
    for y in range(src_img.shape[0]):
        for x in range(src_img.shape[1]):
            if dist_img[y,x] < 0:  # 輪郭の外側
                v = int(255.0 - abs(dist_img[y,x]) * 255.0 / min_val)
                dw_img[y,x] = (0, v, v)
            elif dist_img[y,x] > 0:  # 輪郭の内側
                v = 255 - dist_img[y,x] * 255 / max_val
                dw_img[y,x] = (0, 0, v)
            else:  # 輪郭
                dw_img[y,x] = (255,255,255)

    dw_img2: np.ndarray = np.zeros((height, width, 3), dtype=np.uint8) # 距離と内接円
    dw_img2.fill(255)
    # https://docs.opencv.org/4.x/d6/d6e/group__imgproc__draw.html#ga746c0625f1781f1ffc9056259103edbc
    cv2.drawContours(dw_img2, contours, target_index, (255, 0, 255), -1)
    radius: int = int(max_val)
    cv2.circle(dw_img2, max_loc, radius, (128, 128, 0), 2, cv2.LINE_AA)
    cv2.imshow('dw_img', dw_img)
    cv2.imshow('dw_img2', dw_img2)
    cv2.imshow('Source', src_img)
    cv2.waitKey()


if __name__ == '__main__':
    main()


#  参考 https://emotionexplorer.blog.fc2.com/blog-entry-88.html
