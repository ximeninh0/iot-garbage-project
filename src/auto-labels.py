import os
import json
from utils.Colors import Colors
import shutil
import sys

def check_interval_done(interval,option):

    if interval[0] >= interval[1] or interval[1] <= interval[0]:
        return False
    
    arqv_lines = []
    option -= 1
    with open("src\intervals-list.txt",'r') as f:
        for line in f:
            arqv_lines.append(line.split("\n")[0])

    grb_intervals_str = arqv_lines[option]
    grb_intervals = []
    grb_intervals = grb_intervals_str.split(" ")

    for done_intervals_str in grb_intervals:
        done_intervals = []
        done_intervals = done_intervals_str.split("-")
        if ((interval[0] >= done_intervals[0] and interval[0] <= done_intervals[1]) or
            (interval[1] >= done_intervals[0] and interval[1] <= done_intervals[1])):
            return False
        
    return True

def process_interval(interval, option):




if __name__ == "__main__":
    print("Selecione o tipo de resíduo: ")
    print("[1] biological")
    print("[2] metal")
    print("[3] paper")
    print("[4] plastic")
    option = int(input())

    print("Insira o intervalo das imagens (ex:200-300, 550-750...)")
    interval_str = input()

    interval = []
    interval = interval_str.split("-")
    if not check_interval_done(interval,option):
        Colors.error(f"O intervalo {interval[0]}-{interval[1]} tem imagens já feitas ou é inválido")
        sys.exit()

    process_interval(interval, option)

    


