from ultralytics import YOLO
from multiprocessing import freeze_support

def main():
    model = YOLO("runs/segment/train/weights/best.pt")
    model.val(data="data.yaml", split="test")



if __name__ == "__main__":
    freeze_support()
    main()