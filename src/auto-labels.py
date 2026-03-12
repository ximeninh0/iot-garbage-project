import os
import json

from tqdm.asyncio import tqdm
from utils.Colors import Colors
import shutil
import sys
from ultralytics import YOLO
import cv2 

def check_interval_done(interval,option):

    interval[0] = int(interval[0])
    interval[1] = int(interval[1])

    if interval[0] >= interval[1] or interval[1] <= interval[0]:
        return False
    
    arqv_lines = []
    option -= 1
    with open("src/intervals-list.txt",'r') as f:
        for line in f:
            arqv_lines.append(line.split("\n")[0].split(": ")[1])

    grb_intervals_str = arqv_lines[option]
    grb_intervals = []
    grb_intervals = grb_intervals_str.split(" ")

    for done_intervals_str in grb_intervals:
        done_intervals = []
        done_intervals.append(int(done_intervals_str.split("-")[0]))
        done_intervals.append(int(done_intervals_str.split("-")[1]))

        if ((interval[0] >= done_intervals[0] and interval[0] <= done_intervals[1]) or
            (interval[1] >= done_intervals[0] and interval[1] <= done_intervals[1])):
            return False
        
    arqv_lines[option] += f" {interval[0]}-{interval[1]}"
    with open("src/intervals-list.txt",'w') as f:

        for i,line in enumerate(arqv_lines):
            if i == 0:
                f.write(f"biologico: {line}\n")
            elif i == 1: 
                f.write(f"metal: {line}\n")
            elif i == 2: 
                f.write(f"papel: {line}\n")            
            elif i == 3: 
                f.write(f"plastico: {line}\n")
        i += 1
        
    return True

def process_interval(interval, option, batch):
    raw_path = "data/raw_dataset"
    interval[0] = int(interval[0])
    interval[1] = int(interval[1])

    images_batch = []
    img_names = []

    model = YOLO("grb-model.pt")

    # Configuraçao da barra de progresso
    progress_bar_text = f"{Colors.OKCYAN}Processando Imagens{Colors.ENDC}"
    progress_bar = tqdm(total=interval[1] - interval[0], desc=progress_bar_text, ncols=100)

    i = -1
    batch_counter = 0
    for grb_dirs in os.listdir(raw_path):
        i += 1
        dir_path = os.path.join(raw_path,grb_dirs)
        if grb_dirs == option:
            for filename in os.listdir(dir_path):

                if filename.endswith(".json"):
                    continue

                filenumber = int(filename.split("_")[1].removesuffix(".jpg"))
                if not (filenumber >= interval[0] and filenumber <= interval[1]):
                    continue
                progress_bar.update(1)

                image = cv2.imread(os.path.join(dir_path,filename))

                if batch_counter < batch and filenumber != interval[1]:
                    images_batch.append(image)
                    img_names.append(filename)
                    batch_counter += 1
                else:
                    if filenumber == interval[1]:
                        images_batch.append(image)
                        img_names.append(filename)
                    
                    results = model.predict(source=images_batch, save=False, imgsz=640, conf=0.5, verbose=False)

                    for j,result in enumerate(results):
                        result_image = cv2.imread(os.path.join(dir_path,img_names[j]))
                        height = result_image.shape[0]
                        width = result_image.shape[1]
                        json_name = img_names[j].removesuffix(".jpg") + ".json"
                        data = {
                            "version": "5.10.1",
                            "flags": {},
                            "shapes": [],
                            "imagePath": img_names[j],
                            "imageData": None,
                            "imageHeight": height,
                            "imageWidth": width
                        }
                        classes = result.boxes.cls
                        class_names = result.names
                        boxes = result.boxes.xyxy
                        for k in range(len(classes)):
                            class_id = int(classes[k])
                            box = boxes[k].tolist()
                            shape = {
                                "label": class_names[class_id],
                                "points": [[box[0], box[1]], [box[2], box[3]]],
                                "group_id": None,
                                "shape_type": "rectangle",
                                "flags": {}
                            }
                            data["shapes"].append(shape)

                        with open(os.path.join(dir_path,json_name),"w") as f:
                            json.dump(data,f,indent=4)
                    images_batch = []
                    img_names = []
                    batch_counter = 0

if __name__ == "__main__":
    print("Selecione o tipo de resíduo: ")
    print("[1] biological")
    print("[2] metal")
    print("[3] paper")
    print("[4] plastic")
    option = int(input())
    option_str = ""
    match option:
        case 1:
            option_str = "biological"
        case 2:
            option_str = "metal"
        case 3:
            option_str = "paper"
        case 4:
            option_str = "plastic"
        case _:
            Colors.error("Opção inválida")
            sys.exit()
    print("Insira o intervalo das imagens (ex:200-300, 550-750...)")
    interval_str = input()

    interval = []
    interval = interval_str.split("-")
    if not check_interval_done(interval,option):
        Colors.error(f"O intervalo {interval[0]}-{interval[1]} tem imagens já feitas ou é inválido")
        sys.exit()

    batch = 16
    Colors.info(f"Processando intervalo {interval[0]}-{interval[1]} do tipo {option} em batches de {batch} imagens...")
    process_interval(interval, option_str, batch)
    Colors.success(f"Intervalo {interval[0]}-{interval[1]} do tipo {option} processado com sucesso!")

    


