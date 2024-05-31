#!/data/data/com.termux/files/usr/bin/bash

# Obtener acceso root y copiar los archivos msgstore.db y wa.db de WhatsApp Business
su -c 'cp /data/data/com.whatsapp.w4b/databases/msgstore.db /sdcard/msgstore.db'
su -c 'cp /data/data/com.whatsapp.w4b/databases/wa.db /sdcard/wa.db'
echo "Archivos copiados exitosamente de WhatsApp Business."

# Obtener acceso root y copiar los archivos msgstore.db y wa.db de WhatsApp
su -c 'cp /data/data/com.whatsapp/databases/msgstore.db /sdcard/msgstore.db'
su -c 'cp /data/data/com.whatsapp/databases/wa.db /sdcard/wa.db'
echo "Archivos copiados exitosamente de WhatsApp."
