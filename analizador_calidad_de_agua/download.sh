#!/bin/bash
EC2_HOST="3.92.208.97"
EC2_USER="ec2-user"
RUTA_REMOTA="/home/ec2-user/last_measurement.txt"
RUTA_LOCAL="/mnt/c/Users/andre/TopicosEspeciales2/proyecto_final_redes/analizador_calidad_de_agua/data/new_data"
CLAVE_PEM="/home/andre/.ssh/mi_clave.pem"


echo "Descargando archivo desde $EC2_HOST..."
scp -i "$CLAVE_PEM" "$EC2_USER@$EC2_HOST:$RUTA_REMOTA" "$RUTA_LOCAL"

if [ $? -eq 0 ]; thencd
    echo "Descarga completa"
else
    echo "Error de descarga"
fi