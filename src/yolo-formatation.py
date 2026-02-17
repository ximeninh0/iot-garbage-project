import os
import shutil
from utils.Colors import Colors
import json
import cv2
import random

DIR = "data/raw_dataset"
GRP_DIR = "data/grouped"

TOLERANCE = 1e-6

labels = {
    "biological": 0,
    "plastic": 1,
    "paper": 2,
    "metal": 3
}

os.makedirs(GRP_DIR, exist_ok=True)
os.makedirs(GRP_DIR + "/images", exist_ok=True)
os.makedirs(GRP_DIR + "/labels", exist_ok=True)


def group_images_with_label():
    count = 0
    for root, dirs, files in os.walk(DIR):
        for filename in files:
            if filename.endswith(".json"):
                continue

            imgLabel = filename.removesuffix(".jpg") + ".json"
            if imgLabel not in files:
                continue

            shutil.copy(os.path.join(root,filename),os.path.join(GRP_DIR + "/images",filename))
            shutil.copy(os.path.join(root,imgLabel),os.path.join(GRP_DIR + "/labels",imgLabel))
            count += 1

    Colors.success(f"{count} Imagens com rótulos no total!")

def convert_segmentation_to_bbx(points):
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]

    x_min = min(x_coords)
    x_max = max(x_coords)
    y_min = min(y_coords)
    y_max = max(y_coords)

    return [(x_min, y_min), (x_max, y_max)]

def convert_jsons_to_txts(LABELS_DIR):
    for filename in os.listdir(LABELS_DIR):
        if filename.endswith(".jpg"):
            continue
        with open(os.path.join(LABELS_DIR, filename), 'r') as f:
            data = json.load(f)

        height = data['imageHeight']
        width = data['imageWidth']
        shapes = data['shapes']

        label_lines = []

        for shape in shapes:
            if shape['label'] not in labels:
                Colors.error(f"Label desconhecida: {shape['label']} em {filename}. IGNORANDO SHAPE.")
                continue
            label = labels[shape['label']]
            points = shape['points']
            is_valid_shape = True
            normalized_points = []

            if shape['shape_type'] != 'rectangle':
                points = convert_segmentation_to_bbx(points)

            # Processamento e verificação de cada ponto
            for point in points:
                x_raw, y_raw = point[0], point[1]

                # Se for negativo e muito próximo de zero, força a ser 0
                if x_raw < 0 and abs(x_raw) < TOLERANCE:
                    x_raw = 0.0
                if y_raw < 0 and abs(y_raw) < TOLERANCE:
                    y_raw = 0.0
                
                # Verifica se o ponto está fora dos limites (após o tratamento de zero)
                if x_raw < 0 or x_raw > width or y_raw < 0 or y_raw > height:
                    Colors.error(f"Ponto fora da imagem: [{x_raw:.6f}, {y_raw:.6f}] em {filename}. IGNORANDO SHAPE.")
                    is_valid_shape = False
                    break # Sai do loop de pontos, pois a shape é inválida

                normalized_points.append((x_raw / width, y_raw / height))
            
            # Pula a shape se ela foi considerada inválida
            if not is_valid_shape:
                continue
            
            point_strs = [f"{p[0]:.6f} {p[1]:.6f}" for p in normalized_points]
            label_line = f"{label} " + " ".join(point_strs)
            label_lines.append(label_line)

        label_file_name = filename.replace(".json", ".txt") # Correção da extensão
        label_file_path = os.path.join(LABELS_DIR, label_file_name) 
        with open(label_file_path, 'w') as label_file:
            label_file.write("\n".join(label_lines))

        os.remove(os.path.join(LABELS_DIR,filename))
    Colors.success("Jsons convertidos na pasta grouped!")

def split_folders(FOLDER_PATH):
    output_path = "./data/dataset/"

    # Cria os diretórios de saída train/val
    train_path = os.path.join(output_path, "train/")
    val_path = os.path.join(output_path, "val/")
    os.makedirs(train_path, exist_ok=True)
    os.makedirs(val_path, exist_ok=True)
    os.makedirs(os.path.join(train_path, "images/"), exist_ok=True)
    os.makedirs(os.path.join(train_path, "labels/"), exist_ok=True)
    os.makedirs(os.path.join(val_path, "images/"), exist_ok=True)
    os.makedirs(os.path.join(val_path, "labels/"), exist_ok=True)

    train = 0.8

    images_path = FOLDER_PATH + "/images"
    labels_path = FOLDER_PATH + "/labels"

    images = os.listdir(images_path)
    num_images = len(images)
    num_train = int(num_images * train)

    random.shuffle(images)
    # images = sorted(images)
    train_images = images[:num_train]
    val_images = images[num_train:]

    def get_label_name(img_name):
        """Converte nome da imagem para nome do label, suportando múltiplas extensões"""
        name_without_ext = os.path.splitext(img_name)[0]
        label_name = name_without_ext + ".txt"
        return label_name

    # Move as imagens e labels para os diretórios correspondentes
    for img in train_images:
        # if not img.endswith(".jpg"):
        #     continue
        shutil.copy(os.path.join(images_path, img), os.path.join(train_path, "images/", img))
        label_name = get_label_name(img)
        label_full_path = os.path.join(labels_path, label_name)
        if os.path.exists(label_full_path):
            shutil.copy(label_full_path, os.path.join(train_path, "labels/", label_name))
        else:
            with open(os.path.join(train_path, "labels/", label_name), 'w') as fp:
                pass
            print(f"⚠️  Label não encontrada: {label_name} para imagem {img}")

    for img in val_images:
        # if not img.endswith(".jpg"):
        #     continue
        shutil.copy(os.path.join(images_path, img), os.path.join(val_path, "images/", img))
        label_name = get_label_name(img)
        label_full_path = os.path.join(labels_path, label_name)
        if os.path.exists(label_full_path):
            shutil.copy(label_full_path, os.path.join(val_path, "labels/", label_name))
        else:
            with open(os.path.join(train_path, "labels/", label_name), 'w') as fp:
                pass
            print(f"⚠️  Label não encontrada: {label_name} para imagem {img}")

    print(f"   Split concluído!")
    print(f"   Train: {len(train_images)} imagens")
    print(f"   Val: {len(val_images)} imagens")



if __name__ == "__main__":
    Colors.info("Agrupando Imagens com rótulo em grouped...")
    group_images_with_label()

    Colors.info("Formatando jsons para formato .txt...")
    convert_jsons_to_txts(GRP_DIR + '/labels')

    Colors.info("Separando imagens e labels no formato YOLO (treino | validação)...")
    split_folders(GRP_DIR)


