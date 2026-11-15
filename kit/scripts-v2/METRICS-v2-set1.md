# Metrics

Headline: false-safe labels (a dish holding a listed allergen labelled "No listed allergen found"). Must be 0.

| Model | Split | Cases | Safety recall | False-safe | Hazard dishes missing | Label accuracy | Ask rate (key) | Over-caution | Privacy |
|---|---|---|---|---|---|---|---|---|---|
| app-build2 | development | 16 | 82.2% (166 of 202) | 34 | 2 | 87.7% | 7.6% (9.4%) | 3.5% | 16 of 16 cases pass |
| app-build2 | all | 16 | 82.2% (166 of 202) | 34 | 2 | 87.7% | 7.6% (9.4%) | 3.5% | 16 of 16 cases pass |
| app-build3 | development | 16 | 95.5% (193 of 202) | 6 | 3 | 84.9% | 11.3% (9.4%) | 11.8% | 16 of 16 cases pass |
| app-build3 | all | 16 | 95.5% (193 of 202) | 6 | 3 | 84.9% | 11.3% (9.4%) | 11.8% | 16 of 16 cases pass |
| app-build4 | development | 16 | 97.5% (197 of 202) | 1 | 4 | 82.1% | 14.2% (9.4%) | 16.6% | 16 of 16 cases pass |
| app-build4 | all | 16 | 97.5% (197 of 202) | 1 | 4 | 82.1% | 14.2% (9.4%) | 16.6% | 16 of 16 cases pass |
| app-build5 | development | 16 | 92.6% (187 of 202) | 0 | 15 | 75.0% | 16.4% (9.4%) | 18.9% | 16 of 16 cases pass |
| app-build5 | all | 16 | 92.6% (187 of 202) | 0 | 15 | 75.0% | 16.4% (9.4%) | 18.9% | 16 of 16 cases pass |
| app-final1 | held-out | 8 | 81.9% (77 of 94) | 9 | 8 | 71.0% | 18.3% (11.4%) | 20.0% | 8 of 8 cases pass |
| app-final1 | all | 8 | 81.9% (77 of 94) | 9 | 8 | 71.0% | 18.3% (11.4%) | 20.0% | 8 of 8 cases pass |
| replay-sample | development | 7 | 97.8% (87 of 89) | 1 | 1 | 88.2% | 17.6% (8.6%) | 14.7% | 3 of 7 cases pass |
| replay-sample | all | 7 | 97.8% (87 of 89) | 1 | 1 | 88.2% | 17.6% (8.6%) | 14.7% | 3 of 7 cases pass |

## False-safe labels (every one)

- app-build2 M01: PROFILE-C Chicken Satay
- app-build2 M05: PROFILE-C Moules marinières
- app-build2 M07: PROFILE-C Seaweed Salad
- app-build2 M08: PROFILE-C Dal Tadka
- app-build2 M08: PROFILE-C Vegetable Biryani
- app-build2 M08: PROFILE-C Samosa (2)
- app-build2 M09: PROFILE-A Phở Bò
- app-build2 M09: PROFILE-A Bún Chả Giò
- app-build2 M09: PROFILE-C Bún Chả Giò
- app-build2 M09: PROFILE-C Rau Muống Xào Tỏi
- app-build2 M09: PROFILE-D Rau Muống Xào Tỏi
- app-build2 M10: PROFILE-B Baba Ghanoush
- app-build2 M10: PROFILE-C Baklava (3)
- app-build2 M11: PROFILE-A Marzipan Danish
- app-build2 M11: PROFILE-B Avocado Toast
- app-build2 M11: PROFILE-C Marzipan Danish
- app-build2 M15: PROFILE-C Fried Calamari
- app-build2 M16: PROFILE-C Cole Slaw
- app-build2 M17: PROFILE-A 煎堆
- app-build2 M17: PROFILE-C 蝦餃
- app-build2 M17: PROFILE-C 燒賣
- app-build2 M17: PROFILE-D 蘿蔔糕
- app-build2 M22: PROFILE-A Steamed Bao
- app-build2 M22: PROFILE-A Mango Salad
- app-build2 M22: PROFILE-B Fortune Cookies
- app-build2 M22: PROFILE-C Beef with Oyster Sauce
- app-build2 M22: PROFILE-C Caramel Pork
- app-build2 M22: PROFILE-C Cashew Chicken
- app-build2 M22: PROFILE-C Worcestershire Mushrooms
- app-build2 M22: PROFILE-D Mango Salad
- app-build2 M23: PROFILE-A Stollen with Marzipan
- app-build2 M23: PROFILE-B Panettone Slice
- app-build2 M23: PROFILE-C Sticky Toffee Pudding
- app-build2 M23: PROFILE-C Praline Pecan Cluster
- app-build3 M01: PROFILE-C Chicken Satay
- app-build3 M09: PROFILE-A Phở Bò
- app-build3 M09: PROFILE-C Rau Muống Xào Tỏi
- app-build3 M09: PROFILE-D Rau Muống Xào Tỏi
- app-build3 M11: PROFILE-B Avocado Toast
- app-build3 M17: PROFILE-A 煎堆
- app-build4 M17: PROFILE-D 芒果布甸
- app-final1 M02: PROFILE-A Zuppa del Giorno
- app-final1 M02: PROFILE-B Zuppa del Giorno
- app-final1 M02: PROFILE-C Zuppa del Giorno
- app-final1 M02: PROFILE-D Zuppa del Giorno
- app-final1 M12: PROFILE-A Beef Chili
- app-final1 M12: PROFILE-B Classic Cheeseburger
- app-final1 M12: PROFILE-D Pulled Pork Plate
- app-final1 M18: PROFILE-B Beef Rendang
- app-final1 M18: PROFILE-C Ayam Goreng
- replay-sample M10: PROFILE-B Hummus

## Privacy failures

- replay-sample M01: request 1: body is not a string (dict); request 2: body is not a string (dict); requests of this case differ from each other (2 distinct)
- replay-sample M10: request 1: body is not a string (dict)
- replay-sample M16: request 2: PNG data; request 2: field named 'image' holds data; request 1: no "Dishes:" section
- replay-sample M17: request 1: body is not a string (dict)
