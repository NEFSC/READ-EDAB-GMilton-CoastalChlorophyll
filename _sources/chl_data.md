# Chlorophyll data 

All chlorophyll data was collected from public data repositories and project websites: SeaBASS, CalCOFI, HOTS, SEAMAP, IOOS, CIOOS, WOD, BCO-DMO, Aquamatch, Pan-Arctic, GLOBEC, GLORIA. 

All Chlorophyll data has 2 data type flags
- HPLC flags (0=HPLC used, 1=HPLC not used, 2=HPLC used but mislabled)
- Triplicate flags (0=triplicates recorded, 1=triplicates not recorded)

All data from repositories that do not distinguishe between in vivo and extracted methods (SeaBASS, IOOS, WOD) have an added data_type flag
- data_type_flag (0=extracted or HPLC, 1=in vivo, 2 = unknown)
