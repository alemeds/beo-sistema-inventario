#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para cargar logias de la Gran Logia de la Argentina
Lee credenciales desde .streamlit/secrets.toml
"""

import psycopg2
import re
import toml

# Cargar credenciales desde secrets.toml
try:
    secrets = toml.load('.streamlit/secrets.toml')
    DB_CONFIG = {
        'host': secrets['database']['host'],
        'port': secrets['database']['port'],
        'database': secrets['database']['database'],
        'user': secrets['database']['username'],
        'password': secrets['database']['password'],
        'sslmode': 'require'
    }
except Exception as e:
    print(f"❌ Error al cargar secrets.toml: {e}")
    print("Verifica que el archivo .streamlit/secrets.toml exista y tenga la sección [database]")
    exit(1)

# Logias ZONA 1 - Capital Federal (CABA)
LOGIAS_ZONA1 = """
• UNION DEL PLATA Nro 1 – Trabaja Lunes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• CONFRATERNIDAD ARGENTINA Nro 2 – Trabaja Jueves 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
• CONSUELO DEL INFORTUNIO Nro 3 – Trabaja Martes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• TOLERANCIA Nro 4 – Trabaja Viernes Todos en TTE. GRAL. J. D. PERON 1242 CABA
• REGENERACION Nro 5 – Trabaja Miércoles 1ro 3ro 5to en Av. Boedo N°1115 CABA
• LEALTAD Nro 6 – Trabaja Viernes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• CONSTANCIA Nro 7 – Trabaja Viernes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• SOL DE MAYO Nro 8 – Trabaja Miércoles Todos en TTE. GRAL. J. D. PERON 1242 CABA
• VERDADERA INICIACION Nro 9 – Trabaja Lunes 2do 4to en BOEDO 1115 CABA
• DOCENTE Nro 11 – Trabaja Lunes Todos en BOEDO 1115 CABA
• UNION ITALIANA Nro 12 – Trabaja Lunes Todos en SAN ANTONIO 814 CABA
• OBEDIENCIA A LA LEY Nro 13 – Trabaja Martes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• VERDAD Nro 14 – Trabaja Miércoles Todos en TTE. GRAL. J. D. PERON 1242 CABA
• GERMANIA Nro 19 – Trabaja Viernes 1ro 3ro 5to en SARMIENTO 1334 CABA
• CARIDAD Nro 22 – Trabaja Martes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• ESTRELLA DEL ORIENTE Nro 27 – Trabaja Lunes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• PROGRESO Nro 28 – Trabaja Lunes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• GIORDANO BRUNO Nro 38 – Trabaja Jueves 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• ALIANZA Nro 40 – Trabaja Martes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• SALOMON Nro 43 – Trabaja Jueves 2do 4to en TTE. GRAL. J. D. PERON 949 CABA
• LIBERI PENSATORI Nro 47 – Trabaja Miércoles 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• LIBERTAD Nro 48 – Trabaja Miércoles 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
• GARIBALDI Nro 49 – Trabaja Lunes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• RIVADAVIA Nro 51 – Trabaja Miércoles 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• CONCORDIA Nro 59 – Trabaja Miércoles 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• IGUALDAD Nro 61 – Trabaja Jueves 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• PRIMERA ARGENTINA Nro 62 – Trabaja Viernes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• SAN MARTÍN Nro 68 – Trabaja Lunes 1ro 3ro en Av. Boedo Nº1115 CABA
• HIJOS DEL TRABAJO Nro 74 – Trabaja Martes 1ro 3ro 5to en SAN ANTONIO 814 CABA
• PLATON Nro 92 – Trabaja Lunes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• HIJOS DEL PROGRESO Nro 93 – Trabaja Jueves 1ro 3ro en Av. Santa Fe 1145 CABA
• EUREKA Nro 106 – Trabaja Martes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• GALILEO GALILEI Nro 115 – Trabaja Miércoles 1ro 3ro en Eugenio Garzón 3780 CABA
• UNION ARGENTINA Nro 134 – Trabaja Lunes 2do 4to 5to en TTE. GRAL. J. D. PERON 1242 CABA
• PITAGORAS Nro 159 – Trabaja Viernes 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
• DEMOCRITO Nro 160 – Trabaja Lunes Todos en TTE. GRAL. J. D. PERON 949 CABA
• LAUTARO Nro 167 – Trabaja Lunes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• VOLTAIRE Nro 197 – Trabaja Jueves 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• UNION FRATERNAL Nro 198 – Trabaja Viernes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 949 CABA
• MARIANO MORENO Nro 201 – Trabaja Martes Todos en BOEDO 1115 CABA
• LA ANTORCHA Nro 285 – Trabaja Miércoles 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• MITRE Nro 325 – Trabaja Martes 2do 4to 5to en TTE. GRAL. J. D. PERON 1242 CABA
• LA RAZON Nro 326 – Trabaja Jueves Todos en TTE. GRAL. J. D. PERON 1242 CABA
• RENOVACION Nro 333 – Trabaja Miércoles 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
• BUENOS AIRES Nro 348 – Trabaja Viernes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• UNION JUSTA "257" Nro 351 – Trabaja Miércoles 2do 4to en TTE GRAL J D PERON 1242 CABA
• FRATERNIDAD INTELECTUAL Nro 352 – Trabaja Sábado 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• FRANCISCO DE MIRANDA Nro 358 – Trabaja Jueves 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• RENOVACIÓN UNIVERSAL Nro 365 – Trabaja Jueves 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• RES NON VERBA Nro 366 – Trabaja Jueves 2do 4to en BOUCHARD 644 PISO 1 DEPTO. C CABA
• PROMETEO Nro 367 – Trabaja Martes Todos en TTE. GRAL. J. D. PERON 1242 CABA
• CIENCIA Y TRABAJO Nro 371 – Trabaja Miércoles 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• GRAL. JOSE DE SAN MARTIN Nro 384 – Trabaja Jueves Todos en TTE. GRAL. J. D. PERON 1242 CABA
• UNITAS Nro 387 – Trabaja Miércoles 2do 4to en TTE. GRAL. J. D. PERON 1242 (en aleman) CABA
• PINDOS Nro 388 – Trabaja Lunes 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
• JORGE CANNING Nro 390 – Trabaja Martes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• T. G. MASARYK Nro 391 – Trabaja Lunes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• BERNARDO O'HIGGINS Nro 392 – Trabaja Martes 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
• MINERVA Nro 395 – Trabaja Viernes Todos en BOEDO 1115 CABA
• LEONARDO DA VINCI Nro 396 – Trabaja Viernes 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
• PANAMERICA Nro 397 – Trabaja Jueves 2do 4to 5to en TTE. GRAL. J. D. PERON 1242 CABA
• SOCRATES Nro 398 – Trabaja Viernes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• FLORIDABLANCA Nro 399 – Trabaja Martes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• TEODORO HERZL Nro 402 – Trabaja Martes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• ARARAT Nro 404 – Trabaja Lunes Todos en TTE. GRAL. J. D. PERON 1242 CABA
• JOSE ARTIGAS Nro 422 – Trabaja Jueves Todos en TTE. GRAL. J. D. PERON 1242 CABA
• SENSATEZ Nro 427 – Trabaja Jueves Todos en TTE. GRAL. J. D. PERON 1242 CABA
• JOSE MATIAS ZAPIOLA Nro 433 – Trabaja Jueves 1ro 3ro 5to en BOEDO 1115 CABA
• LIBERTADORES Nro 434 – Trabaja Miércoles 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• CONSCIENCIA Nro 437 – Trabaja Miércoles 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• URARTU Nro 442 – Trabaja Lunes Todos en TTE. GRAL. J. D. PERON 1242 CABA
• CARPE DIEM Nro 443 – Trabaja Lunes 1ro 3ro 5to en BOEDO 1115 CABA
• MEDIODIA EN PUNTO Nro 444 – Trabaja Lunes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• ALMIRANTE GUILLERMO BROWN Nro 445 – Trabaja Martes Todos en TTE. GRAL. J. D. PERON 1242 CABA
• ECUMENICA Nro 449 – Trabaja Miércoles 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• GRAN REUNION AMERICANA Nro 452 – Trabaja Martes Todos en SAN ANTONIO 814 CABA
• DEL PROGRESO 789 Nro 457 – Trabaja Lunes 2do 4to en PERU 1134 CABA
• BADEN POWELL Nro 465 – Trabaja Viernes 1ro 3ro 5to en SAN ANTONIO 814 CABA
• MALVINAS ARGENTINAS Nro 466 – Trabaja Viernes 1ro 3ro en EUGENIO GARZON 3780 CABA
• SALVADOR ALLENDE Nro 469 – Trabaja Jueves 2do 4to en TTE. GRAL. J. D. PERON 949 CABA
• SOLIDARIDAD Nro 472 – Trabaja Viernes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• REPUBLICANA Nro 473 – Trabaja Sábado 1ro 3ro 5to en San Antonio 814 CABA
• PRIMORDIAL Nro 474 – Trabaja Miércoles 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• GUILLERMO RAWSON Nro 476 – Trabaja Viernes Todos en TTE. GRAL. J. D. PERON 1242 CABA
• SAPERE AUDE Nro 502 – Trabaja Viernes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• VICTOR HAYA DE LA TORRE Nro 505 – Trabaja Jueves 1ro 3ro 5to en TTE. GRAL. J.D. PERON 1242 CABA
• JUSTICIA SOCIAL Nro 511 – Trabaja Jueves 1ro 3ro 5to en BOEDO 1115 CABA
• MAQUIAVELO Nro 519 – Trabaja Lunes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• RENOVACION CULTURAL Nro 522 – Trabaja Viernes 2do 4to en SARMIENTO 1334 CABA
• EQUINOCCIO Nro 527 – Trabaja Miércoles 1ro 3ro 5to en BOEDO 1115 CABA
• CABALLEROS RACIONALES Nro 542 – Trabaja Martes 2do 4to 5to en TTE. GRAL. J. D. PERON 1242 CABA
• MANUEL QUIROGA Nro 548 – Trabaja Martes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• ELOY ALFARO Nro 556 – Trabaja Miércoles 1ro 3ro en SARMIENTO 1334 CABA
• LUZ DE SIRIO Nro 558 – Trabaja Jueves 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• CARL GUSTAV JUNG Nro 563 – Trabaja Martes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• LA COLMENA Nro 569 – Trabaja Martes 1ro 3ro en SARMIENTO 1334 CABA
• CIVITAS Nro 575 – Trabaja Sábado 2do 4to en BOEDO 1115 CABA
• LEY 1420 Nro 579 – Trabaja Viernes 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• SIGMUND FREUD Nro 582 – Trabaja Sábado 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• LUX FIDELI Nro 598 – Trabaja Lunes 2do 4to en TTE. GRAL. J. D. PERON 949 CABA
• COOPERACION Nro 603 – Trabaja Jueves 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• UNIDAD NACIONAL Nro 604 – Trabaja Jueves 2do 4to en TTE. GRAL. J. D. PERON 1242 CABA
• JORGE WESOLOWSKI Nro 609 – Trabaja Sábado 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• OBREROS DEL BIEN Nro 612 – Trabaja Jueves 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• FRATERNOS Y LIBRES Nro 614 – Trabaja Martes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• CIRCULO DE LOS ESCIPIONES Nro 616 – Trabaja Miércoles 2do 4to en BOEDO 1115 CABA
• CAMBIO RENOVADOR Y SOSTENIDO Nro 620 – Trabaja Martes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• FUERZA FRATERNAL Nro 630 – Trabaja Martes 2do 4to en Av. Boedo N°1115 CABA
• DE LOS 300 Nro 631 – Trabaja Lunes 1ro 3ro en Av. Santa Fé Nro. 1145 CABA
• HERMANOS DEL ARTE REAL Nro 638 – Trabaja Lunes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• HIPOLITO YRIGOYEN Nro 644 – Trabaja Lunes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• ALBERT SCHWEITZER Nro 645 – Trabaja Viernes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• SIMON BOLIVAR Nro 646 – Trabaja Sábado Todos en TTE. GRAL. J. D. PERON 1242 CABA
• HIJOS DE LA LIBERTAD Nro 648 – Trabaja Lunes 2do 4to 5to en BOUCHARD 630 CABA
• FIAT LUX Nro 652 – Trabaja Jueves 2do 4to en BOEDO 1115 CABA
• PEDRO BONIFACIO PALACIOS Nro 655 – Trabaja Martes Todos en Suarez 465 CABA
• LA GRAN TRIADA Nro 664 – Trabaja Jueves 2do 4to en Tte. Gral. Juan Domingo Perón N°1242 CABA
• LOS BUHOS Nro 666 – Trabaja Martes 2do 4to en AV. SANTA FE 1145 CABA
• RES PUBLICA Nro 672 – Trabaja Lunes 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CABA
• MEMENTO MORI Nro 674 – Trabaja Viernes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 949 CABA
• PRINCIPIO ACTIVO 913 Nro 676 – Trabaja Miércoles 1ro 3ro en Villa Urquiza CABA
• ARTURO JAURETCHE Nro 678 – Trabaja Sábado 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• PARACELSO Nro 682 – Trabaja Sábado 1ro 3ro 5to en TTE. GRAL. J. D. PERON 1242 CABA
• CIUDADANIA UNIVERSAL Nro 684 – Trabaja Jueves 1ro 3ro 5to en BOEDO 1115 CABA
• PRUDENCIA Nro 693 – Trabaja Martes 2do 4to en Arribeños 3619. CABA
• QUATUOR CORONATI ARGENTINA Nro 696 – Trabaja Jueves 2do 4to en TTE. GRAL. J. D. PERON 949 CABA
• NOBLEZA Nro 699 – Trabaja Miércoles Todos en TTE. GRAL. J. D. PERON 1242 CABA
• JUAN DOMINGO PERÓN Nro 704 – Trabaja Lunes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• RICARDO BALBIN Nro 705 – Trabaja Martes 1ro 3ro 5to en TTE. GRAL. J. D. PERON 949 CABA
• POLITEIA Nro 706 – Trabaja Miércoles 2do 4to en Tte. Gral. Juan Domingo Perón N° 949 CABA
• MERCURIO Nro 708 – Trabaja Sábado 2do 4to en Tte Gral. Juan Domingo Perón N°1242 CABA
• LIBRE, JUSTA Y SOBERANA Nro 709 – Trabaja Martes 2do 4to en TTE. GRAL. J. D. PERON 949 CABA
• LIBERTAS Nro 710 – Trabaja Martes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• INFERNALES DE DON MARTÍN MIGUEL DE GÜEMES Nro 731 – Trabaja Jueves 2do 4to en Tte. Gral. Juan Domingo Perón N°949 CIUDAD AUTONOMA DE BUENOS AIRES
• HIJOS DE LA PATRIA Nro 734 – Trabaja Lunes 2do 4to en Bouchard N°630 CIUDAD AUTONOMA DE BUENOS AIRES
• ANTIGUOS LINDEROS Nro 743 – Trabaja Jueves 2do 4to en SAN ANTONIO 814 CABA
• JOSÉ MARÍA PAZ Nro 745 – Trabaja Martes 2do 4to en TTE. GRAL. J. D. PERON 949 CABA
• EDUARDO ABEL JARUF Nro 754 – Trabaja Viernes 1ro 3ro 5to en Tte. Gral. Juan Domingo Perón N°949 CABA
• FREMEN Nro 768 – Trabaja Viernes 2do 4to en Suarez N°465 CABA
• RAFFAELE SCHIPA Nro 773 – Trabaja Sábado 2do 4to en Tte. Gral. Juan Domingo Perón N°1242 CABA
• RENOVACIÓN ESOTÉRICA Nro 777 – Trabaja Miércoles 2do 4to en Habana y Joaquín V. Gonzalez CABA
• DE LA RECONSTRUCCIÓN Nro 794 – Trabaja Miércoles 2do 4to en Av. Boedo Nº1115 CABA
• CRUZ DEL SUR Nro 802 – Trabaja Miércoles 1ro 3ro 5to en TTE. GRAL. J. D. PERON 949 CABA
• ECOS DE MAYO Nro 806 – Trabaja Lunes 1ro 3ro en Av. Santa Fe 1145 CABA
• TRIÁNGULO ROETTIERS DE MONTALEAU Nro 1211 – Trabaja Miércoles 1ro 3ro en TTE. GRAL. J. D. PERON 1242 CABA
"""

# Logias ZONA 2 - Gran Buenos Aires
LOGIAS_ZONA2 = """
• EGALITE HUMANITE FRATERNITE Nro 20 – Trabaja Miércoles 1ro 3ro en AVENIDA DEL LIBERTADOR 3120 La Lucila
• UNIÓN DE SAN FERNANDO Nro 37 – Trabaja Martes 3ro 5to en Constitución N°622 San Fernando
• HIJOS DE LA ALIANZA Nro 45 – Trabaja Miércoles 1ro 3ro en ANCHORENA 486 VICENTE LOPEZ
• DANIEL MARIA CAZON Nro 73 – Trabaja Martes 2do 4to en Avenida Cazon 1258 TIGRE
• LOS PRIMEROS LIBRES DE QUILMES Nro 103 – Trabaja Viernes 2do 4to en Manuel Castro Nº760 Remedios de Escalada
• GIUSEPPE MAZZINI Nro 118 – Trabaja Viernes 1ro 3ro en COLOMBRES 146 LOMAS DE ZAMORA
• UNION DEL PILAR Nro 127 – Trabaja Lunes 2do 4to en COLECT. PANAMERICANA – KM 50- RAMAL PILAR PILAR
• PORTA PIA Nro 132 – Trabaja Miércoles 1ro 3ro en SANTIAGO DEL ESTERO 2561 SAN ISIDRO
• ALBARELLOS Nro 140 – Trabaja Lunes 2do 3ro en Paseo Victorica N°156 TIGRE
• LUMEN Nro 200 – Trabaja Martes 1ro 3ro en Tabaré N°2974 ITUZAINGÓ
• EMILE COMBES Nro 215 – Trabaja Miércoles 1ro 3ro en GARONA 590 LOMAS DE ZAMORA
• COSMOS Nro 226 – Trabaja Jueves 1ro 3ro 5to en COLOMBRES 146 LOMAS DE ZAMORA
• JUAN MARTIN DE PUEYRREDON Nro 251 – Trabaja Lunes 1ro 3ro en Av. Del Libertador N°3120 LA LUCILA
• AUREOLA DE DOMINICO Nro 304 – Trabaja Jueves 2do 3ro 4to en MITRE 4532 VILLA DOMINICO
• SAN ALBANO Nro 409 – Trabaja Miércoles 1ro en COLOMBRES 146 LOMAS DE ZAMORA
• GRAL. JOSÉ DE SAN MARTIN Nro 441 – Trabaja Lunes 1ro 3ro 4to 5to en JUNIN N° 2147 Villa Maipú, SAN MARTIN
• JOSE INGENIEROS Nro 451 – Trabaja Lunes 2do 4to 5to en RIO CUARTO 2750 BELLA VISTA
• HIJOS DE QUILMES Nro 458 – Trabaja Miércoles 1ro 3ro 5to en MITRE 4532 VILLA DOMINICO
• PERSEVERANCIA Y TRABAJO Nro 470 – Trabaja Sábado 2do 4to en Rivadavia N°470 MAXIMO PAZ
• JOSE ROQUE PEREZ Nro 482 – Trabaja Martes 1ro 3ro en AVENIDA SUCRE 1489 SAN ISIDRO
• REMEDIOS DE ESCALADA DE SAN MARTIN Nro 486 – Trabaja Martes 1ro 3ro en Manuel Castro N°760 REMEDIOS DE ESCALADA
• PAIDEIA Nro 500 – Trabaja Jueves 2do 4to en AVENIDA DEL LIBERTADOR 3120 La Lucila
• ALMAFUERTE Nro 507 – Trabaja Jueves 1ro 3ro 5to en Mejico 786 VILLA SARMIENTO
• FRANCISCO JAVIER MUÑIZ Nro 531 – Trabaja Jueves 2do 4to en – TIGRE
• BENITO JUAREZ Nro 552 – Trabaja Martes 2do 4to en TTE. GRAL. J. D. PERON 949 CABA
• CARLOS WILSON Nro 560 – Trabaja Lunes 2do 4to 5to en Manuel Castro N° 760 REMEDIOS DE ESCALADA
• PRO HOMINE Nro 565 – Trabaja Martes 1ro 3ro en PILAR POINT PILAR
• VITRIOL Nro 566 – Trabaja Martes 1ro 3ro 5to en Av. Del Libertador 3118/20 Olivos
• ARMONIA DE FLORENCIO VARELA Nro 570 – Trabaja Viernes 1ro 3ro 5to en MITRE 4532 VILLA DOMINICO
• SAN ISIDRO LABRADOR Nro 573 – Trabaja Miércoles 1ro 3ro en Avenida Victoria 156 Tigre
• EXCELSIOR Nro 583 – Trabaja Miércoles 2do 4to en SANTIAGO DEL ESTERO 2561 MARTINEZ
• FRANK HEPBURN CHEVALLIER BOUTELL Nro 615 – Trabaja Viernes 2do 4to en GARONA 590 LOMAS DE ZAMORA
• LUZ DEL OESTE Nro 617 – Trabaja Lunes Todos en Estanislao del Campo 1021 VILLA SARMIENTO
• PEDRO BENOIT Nro 636 – Trabaja Viernes 2do 4to en Tabaré N°2974 Ituzaingó
• LEANDRO N. ALEM Nro 657 – Trabaja Viernes 2do 4to en MITRE 4532 VILLA DOMINICO
• LEGIONE GARIBALDINA Nro 660 – Trabaja Martes 1ro 3ro 5to en SANTIAGO DEL ESTERO 2561 MARTINEZ
• HERMOGENES RAMOS MEJIA Nro 663 – Trabaja Viernes 1ro 3ro 5to en – HAEDO
• RAUL RICARDO ALFONSIN Nro 677 – Trabaja Lunes 2do 4to en MITRE 4532 VILLA DOMINICO
• LUZ DE ESCOBAR Nro 681 – Trabaja Lunes 1ro 3ro en LOS TILOS 550 ESCOBAR
• CABALLEROS DE LA ORDEN Nro 688 – Trabaja Lunes 2do 4to en Santiago del Estero 2557 Martínez
• EMILIO CASTELAR Nro 694 – Trabaja Jueves 2do 4to en Tabaré N°2974 ITUZAINGÓ
• HIJOS DE LA LUZ Nro 712 – Trabaja Lunes 1ro 3ro en Tabaré N°2974 Ituzaingó
• PLÉYADE Nro 727 – Trabaja Viernes 2do 4to en Av. del Libertador 3120 La Lucila
• SEFIROTH Nro 728 – Trabaja Jueves 1ro 3ro en Estanislao López 623 PILAR
• VORTEX Nro 733 – Trabaja Jueves 1ro 3ro en Av. Maipú N°2188 OLIVOS
• WILLIAM BLAKE Nro 741 – Trabaja Lunes 1ro 3ro en Manuel Castro N°760 Remedios de Escalada
• GENERAL RODRIGUEZ Nro 746 – Trabaja Martes 3ro 5to en Tabaré N°2974 Ituzaingó
• ESTRELLA DE DAVID Nro 750 – Trabaja Sábado 1ro 3ro en Tabaré N°2974 Ituzaingó
• ESTRELLA DE OCCIDENTE Nro 753 – Trabaja Miércoles 2do 4to en Tabaré N°2974 Ituzaingó
• CABALLEROS DEL PLATA Nro 757 – Trabaja Jueves 2do 4to en Santiago del Estero N°2561 Martinez
• MIGUEL SERVERA Nro 758 – Trabaja Jueves 1ro 3ro 5to en Tabaré N°2974 Ituzaingó
• CIUDADANÍA ACTIVA Nro 760 – Trabaja Sábado 2do 4to en Wenceslao de Tata N°4743 Caseros
• PABELLÓN ARGENTINO Nro 762 – Trabaja Sábado 2do 4to en Santiago del Estero 2561 Martínez
• AVIADOR SAINT EXUPÉRY Nro 775 – Trabaja Sábado 2do en Av. Márquez y ruta 8 Villa Sarmiento
• CABALLEROS DEL FÉNIX Nro 784 – Trabaja Martes 2do 4to en Santiago Del Estero Nº2561 San Isidro
• CIUDADANÍA ACTIVA DEL SUR Nro 785 – Trabaja Jueves 1ro 3ro en Manuel Castro Nº760 Remedios de Escalada
• INITIUM LUCIS Nro 792 – Trabaja Miércoles 2do 4to en Estanislao Del Campo Nº1021 Villa Sarmiento
• LUX INDEFICIENS Nro 798 – Trabaja Miércoles 2do 4to en Estanislao Del Campo Nº1021 Villa Sarmiento
• LUJÁN Nro 810 – Trabaja Viernes 1ro 3ro en Colón 633 Luján
• PEREGRINOS Nro 814 – Trabaja Miércoles 2do 4to en MITRE 4532 Villa Domínico
• VANGUARDIA ARGENTINA Nro 815 – Trabaja Jueves 1ro 3ro en Hilarión de la Quintana 3746 Olivos
• TRIANGULO LUZ SABIDURIA VERDAD Nro 1150 – Trabaja Miércoles 1ro 3ro en Ruben Dario s/n esq. Horacio Quiroga San Vicente
• TRIANGULO EDGAR ALLAN POE Nro 1176 – Trabaja Miércoles 1ro 3ro en – Marcos Paz
• TRIANGULO HIJOS DEL COSMOS Nro 1183 – Trabaja Jueves 1ro 3ro 5to en – Monte Grande
• TRIANGULO MARIO GALASSO Nro 1184 – Trabaja Jueves 1ro 3ro 5to en – Lomas de Zamora
• TRIANGULO ÁNGEL HAMILTON Nro 1185 – Trabaja Jueves 1ro 3ro 5to en – Lomas de Zamora
• TRIANGULO JOSÉ CLEMENTE PAZ Nro 1186 – Trabaja Sábado 1ro 3ro 5to en – José C. Paz
• TRIÁNGULO CABALLEROS DEL TRIVIUM Nro 1191 – Trabaja Lunes 1ro 3ro 5to en – La Capilla
• TRIÁNGULO JUAN DE BENAVIDES Nro 1208 – Trabaja Sábado 1ro 3ro en – Benavidez
• TRIÁNGULO HABITER LUMIERE Nro 1227 – Trabaja Sábado 1ro 3ro en Calle 125 bis 467 Jauregui
"""

def parse_logia(line):
    """Parsea una línea de logia y extrae nombre, número, dirección y oriente"""
    line = line.strip().lstrip('•').strip()

    match = re.match(r'(.+?)\s+Nro\s+(\d+)\s+–\s+Trabaja.+?en\s+(.+)$', line, re.IGNORECASE)

    if match:
        nombre = match.group(1).strip()
        numero = int(match.group(2))
        direccion_completa = match.group(3).strip()

        partes = direccion_completa.rsplit(' ', 1)
        if len(partes) == 2:
            direccion = partes[0].strip()
            localidad = partes[1].strip()

            if localidad.upper() in ['CABA', 'CIUDAD']:
                oriente = 'Capital Federal'
                direccion_final = direccion + ', CABA'
            else:
                oriente = localidad.title()
                direccion_final = direccion + ', ' + localidad
        else:
            oriente = 'No especificado'
            direccion_final = direccion_completa

        return {
            'nombre': nombre,
            'numero': numero,
            'oriente': oriente,
            'direccion': direccion_final
        }

    return None

def cargar_logias(logias_text):
    """Carga logias en la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        logias_cargadas = 0
        logias_duplicadas = 0
        logias_error = 0

        for line in logias_text.strip().split('\n'):
            if not line.strip() or not line.strip().startswith('•'):
                continue

            logia = parse_logia(line)

            if logia:
                try:
                    cursor.execute("""
                        INSERT INTO logias (nombre, numero, oriente, direccion)
                        VALUES (%s, %s, %s, %s)
                    """, (logia['nombre'], logia['numero'], logia['oriente'], logia['direccion']))

                    logias_cargadas += 1
                    print(f"✅ Logia '{logia['nombre']}' N°{logia['numero']} - {logia['oriente']}")

                except psycopg2.IntegrityError:
                    conn.rollback()
                    logias_duplicadas += 1
                    print(f"⚠️  Logia '{logia['nombre']}' N°{logia['numero']} ya existe")

                except Exception as e:
                    conn.rollback()
                    logias_error += 1
                    print(f"❌ Error al cargar logia '{logia['nombre']}': {e}")

        conn.commit()
        cursor.close()
        conn.close()

        print("\n" + "="*60)
        print(f"📊 RESUMEN:")
        print(f"   ✅ Cargadas: {logias_cargadas}")
        print(f"   ⚠️  Duplicadas: {logias_duplicadas}")
        print(f"   ❌ Errores: {logias_error}")
        print("="*60)

        return logias_cargadas

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 0

if __name__ == "__main__":
    print("🏛️  CARGADOR DE LOGIAS - GRAN LOGIA DE LA ARGENTINA")
    print("="*60)

    print("\n📍 ZONA 1 - Capital Federal (CABA)")
    print("="*60)
    zona1_cargadas = cargar_logias(LOGIAS_ZONA1)

    print("\n" + "="*60)
    print("📍 ZONA 2 - Gran Buenos Aires")
    print("="*60)
    zona2_cargadas = cargar_logias(LOGIAS_ZONA2)

    print("\n" + "="*60)
    print(f"✅ PROCESO COMPLETADO!")
    print(f"📊 Total logias cargadas: {zona1_cargadas + zona2_cargadas}")
    print("="*60)
