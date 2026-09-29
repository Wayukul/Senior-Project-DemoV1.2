from pyexpat import model

from ultralytics import YOLO
from multiprocessing import freeze_support

from ultralytics import YOLO

def main():
    model = YOLO("yolov8m-seg.pt")

    model.train(
        data="data.yaml",
        epochs=50,
        imgsz=640,        
        batch=4,          

        mosaic=0.3,
        degrees=0,
        fliplr=0.5,
        scale=0.2,

        overlap_mask=True,
        mask_ratio=1,

        hsv_h=0,
        hsv_s=0,
        hsv_v=0,

        patience=30,
    )
    

if __name__ == "__main__":
    freeze_support()
    main()