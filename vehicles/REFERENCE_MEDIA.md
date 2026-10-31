# Vehicle references and existing-model search

All references were used only for observation and dimensions. The shipped GLBs are original procedural geometry. They contain no photo pixels and no CMRL, MTC, Alstom, Ashok Leyland or Indian Railways logos. Attribution below applies to the reference photos, which are not redistributed.

## Existing-model search (2026-10-31)

The Sketchfab API (`/v3/search`) was queried for chennai metro, cmrl, mtc bus, chennai bus, chennai emu, chennai suburban, indian railways emu, icf emu, medha emu, ashok leyland bus and tamil nadu bus. The search covered both downloadable and view-only models.

- **Metro:** "Chennai Metro Subway_3D Modelling" (Manasvini14) is a station or subway scene, not a trainset, and is not downloadable. No CMRL trainset model was found.
- **EMU:** no Chennai suburban EMU model was found.
- **Bus:** no MTC-liveried bus was found. Generic Ashok Leyland Viking and tourist-bus models exist under CC BY ([example](https://sketchfab.com/3d-models/none-4daaa992332f43419f85783a120cea44)). They show older or non-MTC body styles, and downloading them needs a Sketchfab account, so none were imported.
- "Chennai City Bus Shelter" (ramsurya) is CC BY-NC. The NonCommercial term makes it unsuitable here.

Conclusion: no accurate, compatibly licensed model existed, so all three vehicles were generated.

## Dimension and fleet sources

- [CMRL rolling stock](https://chennaimetrorail.org/technology/rolling-stock/): Phase 1 trainsets have four cars (DMC1, TC1, TC2, DMC2), stainless-steel bodies and 25 kV overhead supply.
- CMRL DPR rolling-stock chapter (summary on [Scribd](https://www.scribd.com/document/375540497/8-rolling-stock-maintenace-facilities)): coach size 21.64 m × 2.9 m.
- [Wikipedia: Chennai Suburban Railway](https://en.wikipedia.org/wiki/Chennai_Suburban_Railway): WAU-4 rolling stock built by ICF, BEML and Siemens. The newer stainless MEDHA and AC EMUs are not modelled.
- [IRIMEE EMU electrical reading material](https://rskr.irimee.in/sites/default/files/Reading%20material%20EMU-Electrical.pdf): one motor coach plus two trailers per unit, so a 9-car rake is three units.
- [Wikipedia: Metropolitan Transport Corporation (Chennai)](https://en.wikipedia.org/wiki/Metropolitan_Transport_Corporation_(Chennai)) and Ashok Leyland order notices ([TNSTU 12 m low-floor order](https://www.ashokleyland.com/backend/wp-content/uploads/2024/07/38TNSTUorder.pdf)): MTC's 12 m Ashok Leyland low-floor fleet.

## Reusable visual references (Wikimedia Commons)

| Vehicle | Photo | Author | Licence | Used for |
|---|---|---|---|---|
| Metro | [Alstom Metropolis train-set at Guindy Metro station](https://commons.wikimedia.org/wiki/File:Alstom_Metropolis_train-set_at_Guindy_Metro_station_in_Chennai.jpg) | Arjun1001 | CC BY-SA 4.0 | Cab nose, windscreen, lamp pods, blue eave and waist stripe |
| Metro | [A Chennai Metro train at Alandhur station](https://commons.wikimedia.org/wiki/File:A_Chennai_Metro_train_at_Alandhur_station.jpg) | Vishwa Sundar | CC BY-SA 4.0 | Door leaves, door windows, car numbers on the blue eave, pantograph |
| Metro | [Chennai Metro train arriving at Porur Bypass station](https://commons.wikimedia.org/wiki/File:Chennai_Metro_train_arriving_at_Porur_Bypass_station.jpg) | TamizhanEditor | CC BY-SA 4.0 | Phase 2 contrast (not modelled) |
| EMU | [ChennaiEMUNew](https://commons.wikimedia.org/wiki/File:ChennaiEMUNew.JPG) | VtTN | CC BY-SA 3.0 | Cream and green V cab front, destination LED, unit number plate, diamond pantograph |
| EMU | [Electric Multiple Unit 11043 of Southern Railway](https://commons.wikimedia.org/wiki/File:Electric_Multiple_Uniit_11043_of_Southern_Railway.jpg) | Pbkrish | CC BY-SA 4.0 | Side livery split, louvres, barred windows, open doorways |
| EMU | [EMU at Velachery MRTS](https://commons.wikimedia.org/wiki/File:EMU_at_velachery_MRTS.JPG) | Bharathmeister | CC BY 3.0 | Buffers, headlamp dome, cattle guard |
| Bus | [Ashok Leyland Low Floor Bus](https://commons.wikimedia.org/wiki/File:Ashok_Leyland_Low_Floor_Bus.jpg) | Rithish RK | CC BY-SA 4.0 | Current purple, cyan and white livery, orange pinstripe, black window band, door style, Tamil operator text |
| Bus | [MTC-AshLey-AC-Bus-570S-Velachery](https://commons.wikimedia.org/wiki/File:MTC-AshLey-AC-Bus-570S-Velachery.jpg) | Srikanth Ramakrishnan/BESTpedia | CC BY-SA 4.0 | Front massing, windscreen and LED board proportions |
| Bus | [MTC Bus 21G](https://commons.wikimedia.org/wiki/File:MTC_Bus_21G.JPG) | VtTN | CC BY 3.0 | Route 21G Tambaram destination (older livery, not modelled) |
