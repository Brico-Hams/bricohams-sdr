# BricoHams SDR — avisos

OpenWebRX+ (AGPL-3.0, by Jakob Ketterl and Marat Fayzullin) is NOT included in this
repository: the kit installs it from its upstream sources, under its own licence.

## FT2 (Fast Track 2)

Los modos FT8/FT4/FT2 se basan en los protocolos y algoritmos publicados de WSJT-X
(Copyright © Joe Taylor K1JT, Steve Franke K9AN, Bill Somerville G4WJS y el grupo de
desarrollo WSJT; GNU GPL v3). La implementación de referencia de FT2 utilizada es
Decodium (Copyright © Martino Merola IU8LMC, con permiso expreso del autor para su uso
por BricoHams), distribuida bajo GPLv3:

- https://github.com/iu8lmc/Decodium-4.0-Core-Shannon
- https://github.com/iu8lmc/Decodium-3.0-Shannon

Este repositorio NO incluye código ni binarios de Decodium: `bricohams-ft2 compilar` los
descarga (versión fijada con `FT2_DECODIUM_REF`) y los compila en la máquina del usuario,
que los recibe bajo GPLv3 SIN GARANTÍA. Los scripts de integración de este kit
(`bricohams-ft2*`) solo invocan el programa `decodium-rx` ya compilado.
La tabla LDPC(174,91) procede del artículo «The FT4 and FT8 Communication Protocols» (QEX, 2020).
