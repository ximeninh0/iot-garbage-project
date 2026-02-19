import os
import shutil
from utils.Colors import Colors
import json
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
            
            if points[0][0] < 0 and abs(points[0][0]) < TOLERANCE:
                points[0][0] = 0.0
            if points[0][1] < 0 and abs(points[0][1]) < TOLERANCE:
                points[0][1] = 0.0
            if points[1][0] < 0 and abs(points[1][0]) < TOLERANCE:
                points[1][0] = 0.0
            if points[1][1] < 0 and abs(points[1][1]) < TOLERANCE:
                points[1][1] = 0.0

            if points[0][0] < 0 or points[0][0] > width or points[0][1] < 0 or points[0][1] > height or \
               points[1][0] < 0 or points[1][0] > width or points[1][1] < 0 or points[1][1] > height:
                Colors.error(f"Shape com pontos fora da imagem em {filename}. IGNORANDO SHAPE.")
                is_valid_shape = False

            x_center = (points[0][0] + points[1][0]) / 2.0
            y_center = (points[0][1] + points[1][1]) / 2.0
            box_width = abs(points[1][0] - points[0][0])
            box_height = abs(points[1][1] - points[0][1])

            x_center_norm = x_center / width
            y_center_norm = y_center / height
            box_width_norm = box_width / width
            box_height_norm = box_height / height
            normalized_points = [(x_center_norm, y_center_norm), (box_width_norm, box_height_norm)]

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


