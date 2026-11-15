"""Menu content and allergen facts for the 24 test cases. Pure data, standard library only.

Allergen codes: PEA peanut, TRE tree nut, MIL milk, EGG egg, WHE wheat/gluten, SOY soy, FIS fish, SHE shellfish, SES sesame.
Fact levels: A = Avoid (the printed text names it, or the dish is by definition made with it). Q = Ask the kitchen (a hidden or
variable source: some recipes hold it, the menu does not say). A dish with no fact for a profile's allergens is clean for that profile.
Label rule for a profile: any A in the profile's allergens -> "Avoid"; else any Q -> "Ask the kitchen"; else "No listed allergen found".
Fact source ids are in SOURCES below. PRINTED = the menu line itself. BASIC = obvious ingredient of the named dish (no hidden-source
claim). GEN = general culinary knowledge, no public page was fetched: this is Unverified and is marked in the answer key.
"""

SOURCES = {
    'FDA': ('FDA: the nine major food allergens are milk, eggs, fish, crustacean shellfish, tree nuts, peanuts, wheat, soybeans and sesame',
            'https://www.fda.gov/food/nutrition-food-labeling-and-critical-foods/food-allergies', 'fetched 2026-11-14'),
    'FARE_PEA': ('FARE peanut page: possible sources include sauces such as chili sauce, pesto, mole sauce and salad dressing, egg rolls, chili, marzipan, granola; African, Asian (Chinese, Indian, Indonesian, Thai, Vietnamese) and Mexican restaurant food',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/peanut', 'fetched 2026-11-14'),
    'AAA_PEA': ('Allergy and Anaphylaxis Australia, Peanut page: "satay/satay sauce" is listed under food and drinks to avoid with a peanut allergy',
                'https://allergyfacts.org.au/?p=1039', 'fetched 2026-11-14'),
    'FARE_TRE': ('FARE tree nut page: pesto (often includes pine nuts or walnuts), marzipan/almond paste, praline, gianduja, nut butters',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/tree-nut', 'fetched 2026-11-14'),
    'FARE_FIS': ('FARE fish page: unexpected sources include Worcestershire sauce, Caesar dressing, barbecue sauce, caponata, bouillabaisse, kimchi made with fish sauce; African, Chinese, Indonesian, Thai and Vietnamese dishes can hold hidden fish',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/fish', 'fetched 2026-11-14'),
    'FARE_SES': ('FARE sesame page: tahini, hummus, baba ghanoush, falafel, halvah, sesame oil, Asian cuisine, sushi, dressings and sauces may hold sesame',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/sesame', 'fetched 2026-11-14'),
    'FARE_MIL': ('FARE milk page: ghee, butter, cheese, cream, custard, pudding, yogurt, whey, casein; chocolate and baked goods may hold milk',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/milk', 'fetched 2026-11-14'),
    'FARE_WHE': ('FARE wheat page: soy sauce and surimi sometimes hold wheat; pasta, couscous, batter-fried foods, marinara sauce and sauces/dressings are wheat sources',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/wheat', 'fetched 2026-11-14'),
    'FARE_SOY': ('FARE soy page: soy sauce, miso, tofu, tempeh, edamame; Asian cuisine (Chinese, Indian, Indonesian, Thai, Vietnamese) has high cross-contact risk',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/soy', 'fetched 2026-11-14'),
    'FARE_EGG': ('FARE egg page: mayonnaise, meringue, hollandaise, most commercial pasta, salad dressings, marzipan, nougat, marshmallows, souffle, baked goods',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/egg', 'fetched 2026-11-14'),
    'FARE_SHE': ('FARE shellfish page: bouillabaisse, fish stock, seafood flavoring, surimi; fish stock or fish sauce is sometimes made from krill',
                 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/shellfish', 'fetched 2026-11-14'),
    'PRINTED': ('The menu line itself names the ingredient', '', 'no external source'),
    'BASIC': ('Basic ingredient of the named dish (not a hidden-source claim)', '', 'no external source'),
    'GEN': ('General culinary knowledge, no public page fetched', '', 'UNVERIFIED'),
}

ALLERGENS = {'PEA': 'peanut', 'TRE': 'tree nut', 'MIL': 'milk', 'EGG': 'egg', 'WHE': 'wheat/gluten', 'SOY': 'soy',
             'FIS': 'fish', 'SHE': 'shellfish', 'SES': 'sesame'}

PROFILES = {
    'PROFILE-A': {'name': 'Peanut', 'allergens': ['PEA']},
    'PROFILE-B': {'name': 'Tree nut and sesame', 'allergens': ['TRE', 'SES']},
    'PROFILE-C': {'name': 'Milk, egg, wheat and soy', 'allergens': ['MIL', 'EGG', 'WHE', 'SOY']},
    'PROFILE-D': {'name': 'Fish and shellfish', 'allergens': ['FIS', 'SHE']},
}

LABELS = {'clean': 'No listed allergen found', 'ask': 'Ask the kitchen', 'avoid': 'Avoid'}


def A(code, why, src='PRINTED'):
    return (code, 'A', why, src)


def Q(code, why, src='GEN'):
    return (code, 'Q', why, src)


class En(str):
    pass


def D(name, price, desc='', *facts, sub='', en=''):
    fl = []
    for f in facts:
        if isinstance(f, En):
            en = str(f)
        else:
            fl.append(f)
    return {'name': name, 'price': price, 'desc': desc, 'facts': fl, 'sub': sub, 'en': en}


def ALLQ(why='the menu does not say what is in this dish'):
    return [Q(c, why, 'PRINTED') for c in ALLERGENS]


SOYS = lambda: [A('SOY', 'the menu names soy sauce'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE')]
SOYH = lambda: [Q('SOY', 'stir-fry and marinade sauces commonly use soy sauce; Asian cuisine is flagged for soy', 'FARE_SOY'),
                Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE')]
FISHH = lambda: Q('FIS', 'fish sauce is a common hidden source in this cuisine', 'FARE_FIS')

# Each menu: id, title, lang, font keys, style, heldout, sections [(heading, [dishes])]
MENUS = []


def menu(**kw):
    MENUS.append(kw)


menu(id='M01', title='Bangkok Garden', lang='en', font='georgia', bg='cream', style='clean', heldout=False, sections=[
    ('Starters and salads', [
        D('Spring Rolls', '$8', 'wheat wrapper, cabbage, carrot, sweet chili sauce',
          A('WHE', 'the wrapper is wheat', 'BASIC'), Q('PEA', 'FARE lists egg rolls as a possible peanut source', 'FARE_PEA'), Q('EGG', 'spring roll wrappers can hold egg'), Q('SOY', 'fillings often use soy sauce', 'FARE_SOY')),
        D('Papaya Salad', '$10', 'shredded green papaya, tomato, lime, chili',
          Q('PEA', 'Thai papaya salad is usually topped with crushed peanuts', 'FARE_PEA'), Q('FIS', 'the dressing usually holds fish sauce', 'FARE_FIS'), Q('SHE', 'dried shrimp is a usual ingredient')),
        D('Chicken Satay', '$11', 'grilled skewers, cucumber relish',
          A('PEA', 'satay comes with peanut sauce; satay is listed as a peanut food to avoid', 'AAA_PEA'), Q('SOY', 'the marinade often has soy sauce', 'FARE_SOY')),
        D('Tom Yum Shrimp Soup', '$14', 'lemongrass broth, shrimp, mushrooms',
          A('SHE', 'the menu names shrimp'), FISHH()),
    ]),
    ('Mains and sides', [
        D('Pad Thai', '$15', 'rice noodles, egg, bean sprouts, crushed peanuts, tamarind',
          A('PEA', 'the menu names crushed peanuts'), A('EGG', 'the menu names egg'), FISHH(), Q('SHE', 'dried shrimp is common in pad thai sauce'), Q('SOY', 'Asian cuisine is flagged for soy', 'FARE_SOY')),
        D('Green Curry Chicken', '$16', 'green curry paste, bamboo shoots, basil',
          FISHH(), Q('SHE', 'curry pastes often hold shrimp paste')),
        D('Egg Fried Rice', '$12', 'jasmine rice, egg, scallion, soy sauce',
          A('EGG', 'the menu names egg'), *SOYS()),
        D('Steamed Jasmine Rice', '$3', 'steamed rice'),
        D('Fresh Mango Slices', '$8', 'ripe mango'),
        D('Thai Iced Tea', '$5', 'black tea, sugar, evaporated milk', A('MIL', 'the menu names evaporated milk')),
    ]),
])

menu(id='M02', title='Trattoria Da Marco', lang='it', font='baskerville', bg='white', style='clean', heldout=True, sections=[
    ('Primi', [
        D('Trofie al Pesto', '€ 12', 'pasta fresca di Genova', En('Trofie with pesto'),
          Q('TRE', 'pesto often includes pine nuts or walnuts', 'FARE_TRE'), Q('PEA', 'FARE lists pesto among sauces that may hold peanut', 'FARE_PEA'),
          Q('MIL', 'pesto is usually made with cheese'), A('WHE', 'fresh pasta is wheat', 'BASIC'), Q('EGG', 'fresh pasta often holds egg', 'FARE_EGG')),
        D('Risotto ai Funghi', '€ 14', 'riso Carnaroli, funghi porcini, brodo', en='Mushroom risotto', *[Q('MIL', 'risotto is usually finished with butter or parmesan')]),
        D('Pasta alla Norma', '€ 12', 'pomodoro, melanzane, ricotta salata', En('Pasta alla Norma'),
          A('MIL', 'ricotta salata is a cheese'), A('WHE', 'pasta is wheat', 'BASIC'), Q('EGG', 'pasta may hold egg', 'FARE_EGG')),
        D('Zuppa del Giorno', '€ 6', 'chiedere al cameriere', *ALLQ(), en='Soup of the day'),
    ]),
    ('Secondi e contorni', [
        D('Pizza Margherita', '€ 10', 'pomodoro, mozzarella, basilico', en='Margherita pizza', *[A('MIL', 'mozzarella is a cheese'), A('WHE', 'pizza dough is wheat', 'BASIC')]),
        D('Calamari Fritti', '€ 11', 'anelli di calamaro, farina, limone', En('Fried calamari'),
          A('WHE', 'the menu names flour'), Q('SHE', 'squid is a mollusc, not on the FDA crustacean list; many shellfish plans include it'), Q('EGG', 'batter may hold egg')),
        D('Insalata Rucola e Pomodorini', '€ 8', 'rucola, pomodorini, olio extravergine, limone', en='Rocket and tomato salad'),
        D('Contorno di Patate', '€ 5', 'patate arrosto, sale, rosmarino', en='Roast potatoes'),
    ]),
    ('Dolci', [
        D('Tiramisù', '€ 7', 'mascarpone, savoiardi, caffè, cacao', En('Tiramisu'),
          A('MIL', 'mascarpone is a cheese'), A('EGG', 'tiramisu is made with eggs', 'BASIC'), A('WHE', 'savoiardi are wheat biscuits', 'BASIC')),
        D('Gelato al Pistacchio', '€ 5', 'pistacchio, latte, panna', en='Pistachio gelato', *[A('TRE', 'the menu names pistachio'), A('MIL', 'the menu names milk and cream')]),
        D('Caffè Espresso', '€ 2', 'caffè', en='Espresso'),
    ]),
])

menu(id='M03', title='La Casa de Mole', lang='es', font='trebuchet', bg='kraft', style='photo', heldout=True, sections=[
    ('Platos fuertes', [
        D('Mole Poblano con Pollo', '$165', 'pollo con salsa de chiles y chocolate', En('Chicken with mole poblano'),
          Q('PEA', 'FARE lists mole sauce as a possible peanut source', 'FARE_PEA'), Q('TRE', 'mole recipes often include almonds or other nuts'),
          Q('SES', 'mole recipes often include sesame seeds'), Q('WHE', 'bread or tortilla is often used to thicken mole')),
        D('Tacos de Pescado', '$120', 'pescado empanizado, col, crema', En('Fish tacos'),
          A('FIS', 'the menu names fish'), A('WHE', 'empanizado means breaded'), A('MIL', 'the menu names crema'), Q('EGG', 'breading often uses egg')),
        D('Camarones al Ajillo', '$190', 'camarones, ajo, guajillo', en='Garlic shrimp', *[A('SHE', 'the menu names shrimp')]),
        D('Enchiladas de Queso', '$110', 'tortilla de maíz, queso, salsa roja', en='Cheese enchiladas', *[A('MIL', 'the menu names cheese')]),
    ]),
    ('Entradas y postres', [
        D('Guacamole con Totopos', '$85', 'aguacate, cebolla, cilantro, limón', en='Guacamole with tortilla chips'),
        D('Sopa de Tortilla', '$75', 'caldo de pollo, tortilla, aguacate, chile pasilla', en='Tortilla soup', *[Q('MIL', 'tortilla soup is often served with cheese or cream')]),
        D('Ensalada de Nopales', '$70', 'nopal, jitomate, cebolla, cilantro', en='Cactus salad'),
        D('Churros con Chocolate', '$65', 'masa frita con azúcar y canela', En('Churros with chocolate'),
          A('WHE', 'churros are fried wheat dough', 'BASIC'), Q('EGG', 'dough may hold egg'), Q('MIL', 'chocolate may hold milk', 'FARE_MIL')),
        D('Flan Napolitano', '$70', 'huevo, leche, caramelo', en='Caramel custard', *[A('EGG', 'the menu names egg'), A('MIL', 'the menu names milk')]),
        D('Agua de Horchata', '$35', 'arroz, canela, leche', en='Horchata', *[A('MIL', 'the menu names milk')]),
    ]),
])

menu(id='M04', title='港式小廚', lang='zh', font='hiragino', bg='cream', style='clean', heldout=True, sections=[
    ('熱炒', [
        D('宮保雞丁', 'HK$78', '雞丁、乾辣椒、花生、蔥', A('PEA', 'the menu names peanuts (花生)'), Q('SOY', 'the sauce usually holds soy sauce', 'FARE_SOY'), en='Kung Pao chicken'),
        D('麻婆豆腐', 'HK$62', '豆腐、肉末、豆瓣醬、花椒', A('SOY', 'the menu names tofu (豆腐)'), Q('WHE', 'broad bean paste often holds wheat flour'), en='Mapo tofu'),
        D('蝦仁炒蛋', 'HK$88', '鮮蝦仁、雞蛋', A('SHE', 'the menu names shrimp (蝦仁)'), A('EGG', 'the menu names egg (雞蛋)'), en='Shrimp with scrambled egg'),
        D('揚州炒飯', 'HK$68', '蛋、火腿、蝦仁、青豆', A('EGG', 'the menu names egg (蛋)'), A('SHE', 'the menu names shrimp (蝦仁)'), Q('SOY', 'fried rice is usually seasoned with soy sauce', 'FARE_SOY'), en='Yangzhou fried rice'),
        D('涼拌青瓜', 'HK$38', '青瓜、蒜、醋', en='Cucumber salad'),
    ]),
    ('麵飯點心', [
        D('擔擔麵', 'HK$58', '麵條、肉末、芝麻醬、辣油', A('SES', 'the menu names sesame paste (芝麻醬)'), A('WHE', 'noodles are wheat', 'BASIC'),
          Q('PEA', 'dan dan sauce often holds peanut', 'FARE_PEA'), Q('SOY', 'the sauce often holds soy sauce', 'FARE_SOY'), en='Dan dan noodles'),
        D('蝦餃', 'HK$42', '鮮蝦、澄麵皮', A('SHE', 'the menu names shrimp (鮮蝦)'), Q('WHE', 'the wrapper is wheat starch'), en='Shrimp dumpling'),
        D('芝麻球', 'HK$32', '糯米粉、芝麻、紅豆沙', A('SES', 'the menu names sesame (芝麻)'), en='Sesame ball'),
        D('杏仁豆腐', 'HK$30', '杏仁、牛奶、洋菜', A('TRE', 'the menu names almond (杏仁), which can also mean apricot kernel'), A('MIL', 'the menu names milk (牛奶)'), en='Almond jelly'),
        D('白飯', 'HK$8', '白米飯', en='Steamed rice'),
    ]),
])

menu(id='M05', title='Bistrot du Coin', lang='fr', font='times', bg='white', style='clean', heldout=False, sections=[
    ('Entrées', [
        D("Soupe à l'oignon gratinée", '9 €', 'oignons, bouillon, croûton, gruyère', en='French onion soup', *[A('MIL', 'gruyère is a cheese'), A('WHE', 'croûton is bread')]),
        D('Salade niçoise', '12 €', "thon, anchois, œuf dur, olives, haricots verts", en='Niçoise salad', *[A('FIS', 'the menu names tuna and anchovies'), A('EGG', 'the menu names egg')]),
        D('Quiche lorraine', '11 €', 'lardons, œufs, crème', en='Quiche Lorraine', *[A('EGG', 'the menu names eggs'), A('MIL', 'the menu names cream'), A('WHE', 'the crust is wheat', 'BASIC')]),
        D('Salade verte', '6 €', 'salade, vinaigrette à la moutarde', en='Green salad'),
    ]),
    ('Plats et desserts', [
        D('Sole meunière', '24 €', 'sole, beurre, citron, farine', en='Sole meunière', *[A('FIS', 'the menu names sole'), A('MIL', 'the menu names butter'), A('WHE', 'the menu names flour')]),
        D('Moules marinières', '16 €', 'moules, vin blanc, persil, échalotes', En('Mussels in white wine'),
          Q('SHE', 'mussels are molluscs, not on the FDA crustacean list; many shellfish plans include them'), Q('MIL', 'the sauce is often finished with cream or butter')),
        D('Ratatouille', '11 €', 'aubergine, courgette, tomate, poivron', en='Ratatouille'),
        D('Frites maison', '5 €', 'pommes de terre, sel', en='Fries'),
        D('Crème brûlée', '8 €', "crème, jaune d'œuf, sucre", en='Crème brûlée', *[A('MIL', 'the menu names cream'), A('EGG', 'the menu names egg yolk')]),
        D('Tarte aux amandes', '8 €', "pâte sablée, crème d'amande", En('Almond tart'),
          A('TRE', 'the menu names almond cream'), A('WHE', 'the pastry is wheat', 'BASIC'), Q('EGG', 'pastry and almond cream usually hold egg'), Q('MIL', 'pastry usually holds butter')),
    ]),
])

menu(id='M06', title='Casa Pepe Tapas', lang='es', font='futura', bg='cream', style='clean', heldout=False, sections=[
    ('Tapas', [
        D('Tortilla Española', '8 €', 'huevo, patata, cebolla', en='Spanish omelette', *[A('EGG', 'the menu names egg')]),
        D('Patatas Bravas', '6 €', 'patatas fritas, salsa brava, alioli', en='Spicy potatoes', *[Q('EGG', 'alioli is often made with egg')]),
        D('Croquetas de Jamón', '9 €', 'bechamel, jamón, pan rallado', En('Ham croquettes'),
          A('MIL', 'bechamel is made with milk', 'BASIC'), A('WHE', 'the menu names breadcrumbs (pan rallado)'), Q('EGG', 'the coating usually uses egg')),
        D('Pulpo a la Gallega', '16 €', 'pulpo, pimentón, aceite de oliva', en='Galician octopus', *[Q('SHE', 'octopus is a mollusc, not on the FDA crustacean list; many shellfish plans include it')]),
        D('Ensalada Mixta', '7 €', 'lechuga, tomate, cebolla, atún', en='Mixed salad', *[A('FIS', 'the menu names tuna (atún)')]),
    ]),
    ('Arroces y postres', [
        D('Paella de Mariscos', '18 €', 'arroz, gambas, mejillones, caldo de pescado', en='Seafood paella', *[A('SHE', 'the menu names prawns (gambas)'), A('FIS', 'the menu names fish stock')]),
        D('Gazpacho Andaluz', '7 €', 'tomate, pepino, pimiento, pan', en='Gazpacho', *[A('WHE', 'the menu names bread (pan)')]),
        D('Crema Catalana', '6 €', 'leche, yema, azúcar', en='Catalan custard', *[A('MIL', 'the menu names milk'), A('EGG', 'the menu names egg yolk')]),
        D('Turrón de Almendra', '5 €', 'almendra, miel, clara de huevo', en='Almond nougat', *[A('TRE', 'the menu names almond'), A('EGG', 'the menu names egg white')]),
        D('Agua con Gas', '2 €', 'agua mineral', en='Sparkling water'),
    ]),
])

menu(id='M07', title='Sakura Kitchen', lang='en', font='verdana', bg='white', style='clean', heldout=False, sections=[
    ('Small plates', [
        D('Edamame', '$6', 'steamed soybeans, sea salt', A('SOY', 'edamame are soybeans', 'FARE_SOY')),
        D('Miso Soup', '$4', 'miso, tofu, wakame', A('SOY', 'miso and tofu are soy', 'FARE_SOY'), Q('FIS', 'miso soup is often made with bonito dashi')),
        D('Pork Gyoza', '$8', 'pan-fried dumplings', A('WHE', 'the wrapper is wheat', 'BASIC'), Q('SOY', 'filling and dipping sauce usually hold soy sauce', 'FARE_SOY'), Q('SES', 'gyoza filling and sauce often hold sesame oil', 'FARE_SES')),
        D('Seaweed Salad', '$6', 'wakame, sesame seeds, vinegar', A('SES', 'the menu names sesame seeds'), Q('SOY', 'seaweed salad dressing often holds soy sauce', 'FARE_SOY')),
        D('Cucumber Salad', '$5', 'cucumber, rice vinegar, salt'),
    ]),
    ('Mains', [
        D('Salmon Sashimi', '$18', 'raw salmon, wasabi', A('FIS', 'the menu names salmon')),
        D('Chicken Katsu', '$16', 'panko-breaded cutlet, tonkatsu sauce', A('WHE', 'panko is wheat breadcrumbs'), A('EGG', 'breading uses an egg wash', 'BASIC'), Q('SOY', 'tonkatsu sauce can hold soy')),
        D('Shrimp Tempura', '$14', 'battered shrimp, dipping sauce', A('SHE', 'the menu names shrimp'), A('WHE', 'tempura batter is wheat', 'BASIC'), Q('EGG', 'tempura batter often holds egg'), Q('SOY', 'tempura dipping sauce usually holds soy', 'FARE_SOY')),
        D('Steamed Rice', '$3', 'steamed rice'),
        D('Mochi Ice Cream', '$6', 'rice cake, ice cream', A('MIL', 'ice cream is made with milk', 'BASIC'), Q('EGG', 'ice cream can hold egg')),
    ]),
])

menu(id='M08', title='Spice Route', lang='en', font='futura', bg='cream', style='glare', heldout=False, sections=[
    ('Curries', [
        D('Butter Chicken', '$16', 'tomato cream sauce, butter', A('MIL', 'the menu names cream and butter'), Q('TRE', 'makhani sauce is often thickened with cashew paste')),
        D('Chana Masala', '$13', 'chickpeas, tomato, onion, spices'),
        D('Palak Paneer', '$14', 'spinach, paneer', A('MIL', 'paneer is a cheese')),
        D('Lamb Korma', '$18', 'cashew, cream, yogurt', A('TRE', 'the menu names cashew'), A('MIL', 'the menu names cream and yogurt')),
        D('Dal Tadka', '$12', 'yellow lentils with tempered spices', Q('MIL', 'tadka is often tempered in ghee, which is clarified butter', 'FARE_MIL')),
    ]),
    ('Rice, bread and sweets', [
        D('Vegetable Biryani', '$14', 'basmati rice, vegetables, ghee', A('MIL', 'the menu names ghee', 'FARE_MIL')),
        D('Garlic Naan', '$4', 'baked flatbread, garlic', A('WHE', 'naan is wheat bread', 'BASIC'), Q('MIL', 'naan is often brushed with butter or made with yogurt'), Q('EGG', 'naan dough can hold egg')),
        D('Samosa (2)', '$6', 'pastry, potato, peas', A('WHE', 'the pastry is wheat', 'BASIC')),
        D('Gulab Jamun', '$6', 'fried milk dumplings in syrup', A('MIL', 'the dumplings are made of milk solids', 'FARE_MIL'), Q('WHE', 'the dough usually holds flour')),
        D('Mango Lassi', '$5', 'mango, yogurt', A('MIL', 'the menu names yogurt', 'FARE_MIL')),
    ]),
])

menu(id='M09', title='Phở Saigon', lang='en', font='trebuchet', bg='white', style='clean', heldout=False, sections=[
    ('Noodles and rice', [
        D('Phở Bò', '$14', 'rice noodles, beef broth, herbs', Q('FIS', 'broth and table sauces often hold fish sauce', 'FARE_FIS'), Q('SOY', 'hoisin sauce on the side holds soy', 'FARE_SOY'), Q('PEA', 'hoisin and garnishes can hold peanut; Vietnamese food is flagged', 'FARE_PEA')),
        D('Cơm Tấm Sườn', '$13', 'broken rice, grilled pork, fried egg', A('EGG', 'the menu names fried egg'), Q('FIS', 'the dipping sauce is fish-sauce based', 'FARE_FIS'), Q('SOY', 'the pork marinade usually holds soy sauce', 'FARE_SOY')),
        D('Bún Chả Giò', '$12', 'vermicelli, fried rolls, nước chấm', A('WHE', 'the fried roll wrapper is wheat', 'BASIC'), Q('FIS', 'nước chấm is a fish-sauce dressing', 'FARE_FIS'), Q('PEA', 'fried rolls are flagged as a possible peanut source', 'FARE_PEA'), Q('EGG', 'the wrapper or filling can hold egg')),
        D('Steamed Rice', '$2', 'steamed rice'),
    ]),
    ('Rolls, salads and drinks', [
        D('Bánh Mì Thịt', '$9', 'baguette, pâté, pickled vegetables, mayo', A('WHE', 'the baguette is wheat', 'BASIC'), A('EGG', 'the menu names mayo, which holds egg', 'FARE_EGG'), Q('SOY', 'the seasoning sauce usually holds soy', 'FARE_SOY')),
        D('Gỏi Cuốn', '$8', 'rice paper rolls with shrimp, herbs, peanut dipping sauce', A('SHE', 'the menu names shrimp'), A('PEA', 'the menu names peanut dipping sauce')),
        D('Gỏi Gà', '$11', 'chicken, cabbage, herbs, roasted peanuts', A('PEA', 'the menu names roasted peanuts'), Q('FIS', 'the dressing usually holds fish sauce', 'FARE_FIS')),
        D('Rau Muống Xào Tỏi', '$9', 'morning glory, garlic', Q('FIS', 'stir-fries often use fish sauce', 'FARE_FIS'), Q('SOY', 'stir-fries often use soy sauce', 'FARE_SOY')),
        D('Fresh Fruit Plate', '$6', 'seasonal fruit'),
        D('Cà Phê Sữa Đá', '$5', 'coffee, condensed milk, ice', A('MIL', 'the menu names condensed milk')),
    ]),
])

menu(id='M10', title='Cedar Table', lang='en', font='optima', bg='cream', style='clean', heldout=False, sections=[
    ('Mezze', [
        D('Hummus', '$8', 'chickpeas, lemon, garlic', A('SES', 'hummus is made with tahini (sesame paste)', 'FARE_SES')),
        D('Baba Ghanoush', '$9', 'roasted eggplant, lemon, garlic', A('SES', 'baba ghanoush is made with tahini (sesame paste)', 'FARE_SES')),
        D('Falafel Plate', '$12', 'chickpea fritters, salad', Q('SES', 'falafel is often served with tahini or holds sesame', 'FARE_SES')),
        D('Tabbouleh', '$9', 'parsley, bulgur, tomato, mint', A('WHE', 'bulgur is cracked wheat', 'BASIC')),
        D('Fattoush', '$10', 'romaine, tomato, radish, toasted pita, sumac', A('WHE', 'the menu names pita bread')),
        D('Labneh', '$7', 'strained yogurt, olive oil', A('MIL', 'the menu names yogurt', 'FARE_MIL')),
    ]),
    ('Grill and sweets', [
        D('Chicken Shawarma Plate', '$16', 'marinated chicken, rice, garlic sauce', Q('MIL', 'garlic sauce is sometimes made with yogurt'), Q('SES', 'plates often come with tahini sauce', 'FARE_SES')),
        D('Grilled Lamb Skewers', '$18', 'lamb, onion, pepper'),
        D('Baklava (3)', '$7', 'filo, pistachio, walnut, syrup', A('TRE', 'the menu names pistachio and walnut'), A('WHE', 'filo is wheat pastry', 'BASIC'), Q('MIL', 'baklava is usually brushed with butter', 'FARE_MIL')),
        D('Halva Slice', '$5', 'sweet sesame paste with pistachios', A('SES', 'halva is made of sesame paste', 'FARE_SES'), A('TRE', 'the menu names pistachios')),
    ]),
])

menu(id='M11', title='Sunday Table Café', lang='en', font='palatino', bg='white', style='photo', heldout=False, sections=[
    ('Brunch', [
        D('Buttermilk Pancakes', '$12', 'maple syrup, butter', A('WHE', 'pancakes are wheat', 'BASIC'), A('MIL', 'the menu names buttermilk and butter'), A('EGG', 'pancake batter holds egg', 'FARE_EGG')),
        D('Eggs Benedict', '$15', 'poached eggs, ham, hollandaise, English muffin', A('EGG', 'the menu names eggs and hollandaise', 'FARE_EGG'), A('MIL', 'hollandaise is a butter sauce', 'BASIC'), A('WHE', 'the menu names an English muffin')),
        D('Avocado Toast', '$11', 'seeded sourdough, avocado, lemon', A('WHE', 'sourdough is wheat bread', 'BASIC'), Q('SES', 'seeded bread may hold sesame seeds', 'FARE_SES')),
        D('Granola Bowl', '$10', 'granola, yogurt, berries', A('MIL', 'the menu names yogurt'), Q('TRE', 'granola often holds nuts'), Q('PEA', 'FARE lists granola as a possible peanut source', 'FARE_PEA'), Q('WHE', 'granola is often made with wheat or cross-contact')),
        D('Fresh Fruit Salad', '$8', 'melon, berries, citrus'),
    ]),
    ('Bakery and sides', [
        D('Almond Croissant', '$5', 'almond cream, flaked almonds', A('TRE', 'the menu names almonds'), A('WHE', 'croissants are wheat', 'BASIC'), A('MIL', 'croissants are made with butter', 'BASIC'), Q('EGG', 'almond cream and glaze often hold egg')),
        D('Marzipan Danish', '$5', 'marzipan, pastry', A('TRE', 'marzipan is almond paste', 'FARE_TRE'), A('WHE', 'the pastry is wheat', 'BASIC'), Q('PEA', 'FARE lists marzipan as a possible peanut source', 'FARE_PEA'), Q('EGG', 'marzipan and pastry often hold egg', 'FARE_EGG'), Q('MIL', 'pastry usually holds butter', 'FARE_MIL')),
        D('Crispy Hash Browns', '$5', 'shredded potato, salt'),
        D('Bacon Strips', '$4', 'smoked bacon'),
        D('Orange Juice', '$4', 'fresh squeezed orange juice'),
    ]),
])

menu(id='M12', title="Rosie's Diner", lang='en', font='courier', bg='cream', style='clean', heldout=True, sections=[
    ('Plates', [
        D('Classic Cheeseburger', '$13', 'beef patty, cheddar, bun, pickles', A('MIL', 'cheddar is a cheese'), A('WHE', 'the bun is wheat', 'BASIC'), Q('EGG', 'buns can hold egg'), Q('SES', 'burger buns are often topped with sesame', 'FARE_SES')),
        D('Caesar Salad', '$11', 'romaine, croutons, parmesan, Caesar dressing', Q('FIS', 'FARE lists Caesar dressing as a source of fish (anchovy)', 'FARE_FIS'), Q('EGG', 'Caesar dressing usually holds egg', 'FARE_EGG'), A('MIL', 'the menu names parmesan'), A('WHE', 'croutons are bread')),
        D('Worcestershire Glazed Chicken Sandwich', '$14', 'grilled chicken, Worcestershire glaze, brioche', Q('FIS', 'FARE lists Worcestershire sauce as a source of fish (anchovy)', 'FARE_FIS'), A('WHE', 'brioche is wheat bread', 'BASIC'), A('EGG', 'brioche is made with egg', 'BASIC'), Q('MIL', 'brioche usually holds butter')),
        D('Pulled Pork Plate', '$15', 'slow-cooked pork, house BBQ sauce, slaw', Q('FIS', 'FARE lists barbecue sauce as a possible fish source', 'FARE_FIS'), Q('EGG', 'slaw dressing usually holds mayonnaise', 'FARE_EGG')),
        D('Beef Chili', '$9', 'beef, beans, tomatoes, chili spices', Q('PEA', 'FARE lists chili as a possible peanut source', 'FARE_PEA')),
        D('Grilled Steak', '$24', '8 oz sirloin, sea salt, black pepper'),
    ]),
    ('Sides and sweets', [
        D('Hand-Cut Fries', '$5', 'russet potatoes, sea salt'),
        D('Garden Salad', '$8', 'lettuce, tomato, cucumber, oil and vinegar'),
        D('Vanilla Milkshake', '$7', 'ice cream, milk', A('MIL', 'the menu names ice cream and milk')),
        D('Chocolate Layer Cake', '$8', 'chocolate cake, chocolate frosting', A('WHE', 'cake is wheat', 'BASIC'), A('EGG', 'cake is made with egg', 'BASIC'), A('MIL', 'frosting and cake usually hold butter or milk', 'FARE_MIL')),
    ]),
])

menu(id='M13', title='Seoul Table', lang='en', font='arialr', bg='white', style='clean', heldout=False, sections=[
    ('Rice and stews', [
        D('Bibimbap', '$15', 'rice, vegetables, fried egg, sesame oil, gochujang', A('EGG', 'the menu names fried egg'), A('SES', 'the menu names sesame oil'), Q('SOY', 'gochujang is fermented with soybean', 'FARE_SOY'), Q('WHE', 'gochujang can hold wheat')),
        D('Kimchi Stew', '$14', 'kimchi, pork, tofu', A('SOY', 'the menu names tofu', 'FARE_SOY'), Q('FIS', 'kimchi is often made with fish sauce', 'FARE_FIS'), Q('SHE', 'kimchi is often made with salted shrimp')),
        D('Steamed Rice', '$3', 'steamed rice'),
        D('Barley Tea', '$3', 'roasted barley tea', Q('WHE', 'barley contains gluten', 'BASIC')),
    ]),
    ('Grill and snacks', [
        D('Bulgogi', '$18', 'beef marinated in soy sauce, pear, sesame', *SOYS(), A('SES', 'the menu names sesame')),
        D('Japchae', '$13', 'sweet potato noodles, vegetables, soy sauce, sesame oil', *SOYS(), A('SES', 'the menu names sesame oil')),
        D('Tteokbokki', '$11', 'rice cakes, fish cake, chili sauce', A('FIS', 'the menu names fish cake'), Q('SOY', 'the chili sauce often holds soy', 'FARE_SOY'), Q('WHE', 'fish cake and sauce often hold wheat', 'FARE_WHE')),
        D('Seafood Pancake', '$14', 'scallion, squid, shrimp, flour batter', A('SHE', 'the menu names shrimp'), A('WHE', 'the menu names flour batter'), Q('EGG', 'the batter often holds egg')),
        D('Hotteok', '$6', 'sweet pancake with brown sugar and peanut filling', A('PEA', 'the menu names peanut filling'), A('WHE', 'pancake dough is wheat', 'BASIC'), Q('MIL', 'the dough may hold milk')),
        D('Cold Cucumber Salad', '$5', 'cucumber, vinegar, chili flakes'),
    ]),
])

menu(id='M14', title='ครัวไทยบ้านสวน', lang='th', font='ayuthaya', bg='cream', style='glare', heldout=True, sections=[
    ('อาหารจานเดียว', [
        D('ผัดไทยกุ้ง', '฿120', 'เส้นจันท์ผัด ไข่ ถั่วลิสงป่น กุ้งสด', A('PEA', 'the menu names ground peanuts (ถั่วลิสง)'), A('EGG', 'the menu names egg (ไข่)'), A('SHE', 'the menu names shrimp (กุ้ง)'), Q('FIS', 'pad thai sauce usually holds fish sauce', 'FARE_FIS'), sub='Pad Thai Goong', en='Pad Thai with shrimp'),
        D('ข้าวผัดไข่', '฿70', 'ข้าว ไข่ ต้นหอม ซีอิ๊ว', A('EGG', 'the menu names egg (ไข่)'), A('SOY', 'the menu names soy sauce (ซีอิ๊ว)'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE'), en='Egg fried rice'),
        D('แกงเขียวหวานไก่', '฿110', 'พริกแกงเขียวหวาน ไก่ มะเขือ', Q('FIS', 'curry pastes often hold fish sauce or shrimp paste', 'FARE_FIS'), Q('SHE', 'curry pastes often hold shrimp paste'), sub='Green Curry', en='Green curry with chicken'),
        D('ข้าวสวย', '฿15', 'ข้าวหอมมะลิ', sub='Steamed Rice', en='Steamed rice'),
    ]),
    ('ยำ ต้ม ทอด', [
        D('ส้มตำไทย', '฿80', 'มะละกอ มะเขือเทศ ถั่วฝักยาว', Q('PEA', 'Thai papaya salad is usually topped with peanuts', 'FARE_PEA'), Q('FIS', 'the dressing usually holds fish sauce', 'FARE_FIS'), Q('SHE', 'dried shrimp is a usual ingredient'), en='Papaya salad'),
        D('ไก่สะเต๊ะ', '฿90', 'ไก่ย่างเสียบไม้ น้ำจิ้ม', A('PEA', 'satay comes with peanut sauce; satay is listed as a peanut food to avoid', 'AAA_PEA'), Q('SOY', 'the marinade often has soy sauce', 'FARE_SOY'), sub='Chicken Satay', en='Chicken satay'),
        D('ต้มยำกุ้ง', '฿150', 'ซุปน้ำใส กุ้ง เห็ด ตะไคร้', A('SHE', 'the menu names shrimp (กุ้ง)'), Q('FIS', 'tom yum is often seasoned with fish sauce', 'FARE_FIS'), en='Tom yum shrimp soup'),
        D('ปีกไก่ทอดน้ำปลา', '฿95', 'ปีกไก่ทอด น้ำปลา กระเทียม', A('FIS', 'the menu names fish sauce (น้ำปลา)'), Q('WHE', 'the frying coating often holds flour'), sub='Fried Wings with Fish Sauce', en='Fried chicken wings with fish sauce'),
        D('ผลไม้สด', '฿60', 'ผลไม้ตามฤดูกาล', sub='Fresh Fruit', en='Fresh fruit'),
        D('ชาเย็น', '฿45', 'ชา น้ำตาล นมข้นหวาน', A('MIL', 'the menu names sweetened condensed milk (นมข้นหวาน)'), sub='Thai Iced Tea', en='Thai iced tea'),
    ]),
])

menu(id='M15', title='Luigi’s Kitchen', lang='en', font='palatino', bg='white', style='scan', heldout=False, sections=[
    ('Pasta', [
        D('Fettuccine Alfredo', '$16', 'fresh fettuccine, butter, cream, parmesan', A('MIL', 'the menu names butter, cream and parmesan'), A('WHE', 'pasta is wheat', 'BASIC'), Q('EGG', 'fresh pasta usually holds egg', 'FARE_EGG')),
        D('Pesto Gnocchi', '$15', 'potato gnocchi, basil pesto', Q('TRE', 'pesto often includes pine nuts or walnuts', 'FARE_TRE'), Q('PEA', 'FARE lists pesto as a possible peanut source', 'FARE_PEA'), Q('MIL', 'pesto is usually made with cheese'), A('WHE', 'gnocchi dough holds wheat flour', 'BASIC'), Q('EGG', 'gnocchi dough often holds egg', 'FARE_EGG')),
        D('Spaghetti Marinara', '$13', 'spaghetti, tomato sauce, garlic', A('WHE', 'spaghetti is wheat', 'BASIC'), Q('EGG', 'pasta may hold egg', 'FARE_EGG')),
        D('Minestrone', '$8', 'vegetables, beans, small pasta', A('WHE', 'the menu names pasta'), Q('EGG', 'pasta may hold egg', 'FARE_EGG')),
    ]),
    ('Antipasti, mains and dolci', [
        D('Caprese Salad', '$11', 'tomato, fresh mozzarella, basil, olive oil', A('MIL', 'mozzarella is a cheese')),
        D('Arugula Salad', '$9', 'arugula, lemon, olive oil, shaved parmesan', A('MIL', 'the menu names parmesan')),
        D('Fried Calamari', '$12', 'lightly floured squid, marinara', A('WHE', 'the menu names flour'), Q('SHE', 'squid is a mollusc, not on the FDA crustacean list; many shellfish plans include it'), Q('EGG', 'batter may hold egg')),
        D('Grilled Branzino', '$26', 'whole fish, lemon, herbs', A('FIS', 'the menu names fish')),
        D('Pistachio Gelato', '$6', 'pistachio, milk, cream', A('TRE', 'the menu names pistachio'), A('MIL', 'the menu names milk and cream')),
        D('Panna Cotta', '$7', 'cream, sugar, vanilla, berry sauce', A('MIL', 'the menu names cream')),
    ]),
])

menu(id='M16', title='Harbor House Seafood', lang='en', font='rockwell', bg='white', style='clean', heldout=False, sections=[
    ('Raw bar and starters', [
        D('Shrimp Cocktail', '$15', 'chilled shrimp, cocktail sauce, lemon', A('SHE', 'the menu names shrimp')),
        D('Clam Chowder', '$9', 'clams, potato, cream, bacon', A('MIL', 'the menu names cream'), Q('SHE', 'clams are molluscs, not on the FDA crustacean list; many shellfish plans include them'), Q('WHE', 'chowder is usually thickened with flour', 'FARE_WHE')),
        D('Caesar Salad', '$11', 'romaine, croutons, parmesan, Caesar dressing', Q('FIS', 'FARE lists Caesar dressing as a source of fish (anchovy)', 'FARE_FIS'), Q('EGG', 'Caesar dressing usually holds egg', 'FARE_EGG'), A('MIL', 'the menu names parmesan'), A('WHE', 'croutons are bread')),
        D('Cole Slaw', '$4', 'cabbage, carrot, creamy dressing', Q('EGG', 'creamy dressings usually hold mayonnaise', 'FARE_EGG'), Q('MIL', 'creamy dressings may hold milk or buttermilk')),
    ]),
    ('Mains and desserts', [
        D('Fish and Chips', '$19', 'battered cod, fries, tartar sauce', A('FIS', 'the menu names cod'), A('WHE', 'the batter is wheat', 'BASIC'), A('EGG', 'tartar sauce is mayonnaise based', 'FARE_EGG'), Q('MIL', 'the batter may hold milk')),
        D('Grilled Salmon', '$26', 'salmon fillet, lemon, steamed vegetables', A('FIS', 'the menu names salmon')),
        D('Lobster Roll', '$28', 'lobster, mayo, buttered roll', A('SHE', 'the menu names lobster'), A('WHE', 'the roll is wheat', 'BASIC'), A('EGG', 'the menu names mayo', 'FARE_EGG'), A('MIL', 'the menu names butter')),
        D('Cioppino', '$30', 'tomato broth with shrimp, crab and white fish', A('SHE', 'the menu names shrimp and crab'), A('FIS', 'the menu names white fish')),
        D('Steamed Rice', '$3', 'steamed rice'),
        D('Key Lime Pie', '$8', 'lime custard, graham crust', A('MIL', 'the custard holds condensed milk', 'BASIC'), A('EGG', 'the custard holds egg yolk', 'BASIC'), A('WHE', 'the graham crust is wheat', 'BASIC')),
    ]),
])

menu(id='M17', title='龍門茶樓 Dragon Gate Dim Sum', lang='zh', font='hiragino', bg='cream', style='photo', heldout=False, sections=[
    ('點心', [
        D('蝦餃', '$38', '鮮蝦、澄麵皮', A('SHE', 'the menu names shrimp (鮮蝦)'), Q('WHE', 'the wrapper is wheat starch'), sub='Har Gow', en='Shrimp dumpling'),
        D('燒賣', '$36', '豬肉、蝦、冬菇', A('SHE', 'the menu names shrimp (蝦)'), A('WHE', 'the wrapper is wheat', 'BASIC'), Q('EGG', 'the wrapper may hold egg'), Q('SOY', 'the filling is usually seasoned with soy sauce', 'FARE_SOY'), sub='Siu Mai', en='Pork and shrimp dumpling'),
        D('叉燒包', '$32', '叉燒、麵包皮', A('WHE', 'the bun is wheat', 'BASIC'), Q('SOY', 'char siu sauce holds soy sauce', 'FARE_SOY'), sub='Char Siu Bao', en='BBQ pork bun'),
        D('鮮蝦腸粉', '$42', '鮮蝦、米漿、豉油', A('SHE', 'the menu names shrimp (鮮蝦)'), A('SOY', 'the menu names soy sauce (豉油)'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE'), sub='Shrimp Rice Roll', en='Shrimp rice noodle roll'),
        D('蘿蔔糕', '$30', '白蘿蔔、米粉、臘腸', Q('SHE', 'turnip cake often holds dried shrimp'), Q('SOY', 'turnip cake is usually served with soy sauce', 'FARE_SOY'), sub='Turnip Cake', en='Turnip cake'),
    ]),
    ('甜品及其他', [
        D('煎堆', '$28', '糯米粉、芝麻、豆沙', A('SES', 'the menu names sesame (芝麻)'), Q('PEA', 'fillings can hold peanut paste', 'FARE_PEA'), sub='Sesame Balls', en='Sesame balls'),
        D('蛋撻', '$26', '蛋漿、酥皮', A('EGG', 'the menu names egg custard (蛋漿)'), A('WHE', 'the pastry is wheat', 'BASIC'), Q('MIL', 'the custard or pastry may hold milk or butter', 'FARE_MIL'), sub='Egg Tart', en='Egg tart'),
        D('芒果布甸', '$28', '芒果、淡奶、魚膠粉', A('MIL', 'the menu names evaporated milk (淡奶)'), A('FIS', 'the menu names fish gelatin (魚膠粉)', 'FARE_FIS'), sub='Mango Pudding', en='Mango pudding'),
        D('白粥', '$12', '白米、水、薑', sub='Plain Congee', en='Plain congee'),
        D('白灼生菜', '$34', '生菜、蒜、油', sub='Blanched Lettuce', en='Blanched lettuce'),
    ]),
])

menu(id='M18', title='Warung Nusantara', lang='en', font='gill', bg='kraft', style='clean', heldout=True, sections=[
    ('Satay and snacks', [
        D('Satay Ayam', '$9', 'chicken skewers, peanut sauce', A('PEA', 'the menu names peanut sauce; satay is listed as a peanut food to avoid', 'AAA_PEA'), Q('SOY', 'the marinade often has soy sauce', 'FARE_SOY')),
        D('Gado-Gado', '$10', 'blanched vegetables, tofu, tempeh, egg, peanut sauce', A('PEA', 'the menu names peanut sauce'), A('SOY', 'the menu names tofu and tempeh', 'FARE_SOY'), A('EGG', 'the menu names egg')),
        D('Pisang Goreng', '$5', 'banana fritters', A('WHE', 'fritter batter is wheat flour', 'BASIC'), Q('EGG', 'batter may hold egg')),
        D('Roti Canai', '$5', 'flaky flatbread, curry dip', A('WHE', 'flatbread is wheat', 'BASIC'), Q('MIL', 'roti dough is often made with ghee or butter', 'FARE_MIL'), Q('EGG', 'roti dough often holds egg')),
    ]),
    ('Rice and noodles', [
        D('Nasi Goreng', '$11', 'fried rice, fried egg, sweet soy sauce, chicken', A('EGG', 'the menu names fried egg'), *SOYS(), Q('SHE', 'nasi goreng is often cooked with shrimp paste')),
        D('Mee Goreng', '$11', 'fried yellow noodles, egg, vegetables, chili sauce', A('WHE', 'wheat noodles', 'BASIC'), A('EGG', 'the menu names egg'), Q('SOY', 'fried noodle sauces usually hold soy', 'FARE_SOY'), Q('PEA', 'chili sauce can hold peanut; Indonesian food is flagged', 'FARE_PEA')),
        D('Laksa', '$13', 'noodle soup, prawns, tofu puffs, chili paste', A('SHE', 'the menu names prawns'), A('SOY', 'tofu puffs are soy', 'FARE_SOY'), Q('FIS', 'laksa paste often holds fish or shrimp paste', 'FARE_FIS')),
        D('Beef Rendang', '$15', 'slow-cooked beef in spices and coconut', Q('TRE', 'some rendang pastes use candlenut or ground nuts')),
        D('Ayam Goreng', '$12', 'fried chicken with turmeric and rice', Q('WHE', 'the frying coating often holds flour')),
        D('Es Teh Manis', '$3', 'sweet iced tea'),
    ]),
])

menu(id='M19', title='Flour & Chalk Bakery', lang='en', font='chalk', bg='chalk', style='clean', heldout=False, sections=[
    ('Bakes', [
        D('Banana Bread', '$4', 'banana, flour, butter, eggs, walnuts', A('WHE', 'the menu names flour'), A('MIL', 'the menu names butter'), A('EGG', 'the menu names eggs'), A('TRE', 'the menu names walnuts')),
        D('Oat Cookie', '$3', 'oats, brown sugar, butter, raisins', A('MIL', 'the menu names butter'), Q('WHE', 'cookies usually hold flour or oats with wheat cross-contact'), Q('EGG', 'cookies usually hold egg', 'FARE_EGG')),
        D('Nutella Crêpe', '$7', 'thin pancake, hazelnut chocolate spread', A('TRE', 'the menu names hazelnut spread (gianduja)', 'FARE_TRE'), A('WHE', 'crêpes are wheat', 'BASIC'), A('EGG', 'crêpe batter holds egg', 'BASIC'), Q('MIL', 'the spread and batter usually hold milk', 'FARE_MIL')),
        D('Sourdough Slice', '$3', 'sourdough, butter', A('WHE', 'sourdough is wheat bread', 'BASIC'), A('MIL', 'the menu names butter')),
    ]),
    ('Lunch and drinks', [
        D('Hummus and Veggie Wrap', '$9', 'hummus, cucumber, tomato, tortilla', A('SES', 'hummus is made with tahini (sesame paste)', 'FARE_SES'), A('WHE', 'the tortilla is wheat', 'BASIC')),
        D('Tuna Sandwich', '$8', 'tuna, mayo, bread', A('FIS', 'the menu names tuna'), A('EGG', 'the menu names mayo', 'FARE_EGG'), A('WHE', 'the menu names bread')),
        D('Fruit Cup', '$5', 'melon, grapes, pineapple'),
        D('Green Smoothie', '$6', 'spinach, banana, apple, water'),
        D('Black Coffee', '$3', 'brewed coffee'),
    ]),
])

menu(id='M20', title='El Camino Tex-Mex', lang='en', font='verdana', bg='white', style='blur', heldout=False, sections=[
    ('Platos', [
        D('Chicken Fajitas', '$17', 'grilled chicken, peppers, onions, flour tortillas', A('WHE', 'the menu names flour tortillas'), Q('SOY', 'fajita marinades often hold soy sauce', 'FARE_SOY')),
        D('Beef Burrito', '$14', 'beef, rice, beans, cheese, flour tortilla', A('MIL', 'the menu names cheese'), A('WHE', 'the menu names a flour tortilla')),
        D('Chicken Mole Enchiladas', '$16', 'corn tortillas, chicken, mole, queso fresco', Q('PEA', 'FARE lists mole sauce as a possible peanut source', 'FARE_PEA'), Q('TRE', 'mole recipes often include almonds or other nuts'), Q('SES', 'mole recipes often include sesame seeds'), A('MIL', 'the menu names queso fresco')),
        D('Loaded Nachos', '$12', 'tortilla chips, cheese sauce, jalapeño', A('MIL', 'the menu names cheese sauce')),
        D('Elote', '$6', 'grilled corn, mayo, cotija cheese, chili', A('MIL', 'the menu names cotija cheese'), A('EGG', 'the menu names mayo', 'FARE_EGG')),
    ]),
    ('Sides and sweets', [
        D('Chips and Salsa', '$5', 'corn chips, tomato salsa'),
        D('Black Bean Soup', '$7', 'black beans, onion, cumin, lime'),
        D('Flan', '$7', 'caramel custard', A('MIL', 'custard is made with milk', 'FARE_MIL'), A('EGG', 'custard is made with egg', 'BASIC')),
        D('Tres Leches Cake', '$8', 'sponge cake soaked in three milks', A('MIL', 'the menu names milks'), A('EGG', 'sponge cake holds egg', 'BASIC'), A('WHE', 'cake is wheat', 'BASIC')),
        D('Cilantro Lime Rice', '$4', 'rice, cilantro, lime'),
    ]),
])

menu(id='M21', title='Olive & Thyme Greek Kitchen', lang='en', font='cochin', bg='cream', style='clean', heldout=True, sections=[
    ('Mezedes', [
        D('Spanakopita', '$9', 'spinach and feta pie', A('WHE', 'the pie is wrapped in wheat filo', 'BASIC'), A('EGG', 'spanakopita filling holds egg', 'BASIC'), A('MIL', 'the menu names feta cheese')),
        D('Greek Salad', '$10', 'tomato, cucumber, olives, feta, oregano', A('MIL', 'the menu names feta')),
        D('Hummus', '$7', 'chickpeas, lemon, olive oil', A('SES', 'hummus is made with tahini (sesame paste)', 'FARE_SES')),
        D('Dolmades', '$8', 'vine leaves, rice, herbs, lemon'),
    ]),
    ('Mains and sweets', [
        D('Moussaka', '$17', 'eggplant, spiced lamb, béchamel', A('MIL', 'béchamel is made with milk', 'BASIC'), A('WHE', 'béchamel is thickened with flour', 'BASIC'), Q('EGG', 'béchamel topping often holds egg')),
        D('Chicken Souvlaki Pita', '$13', 'grilled chicken, pita, tomato, onion', A('WHE', 'pita is wheat bread', 'BASIC'), Q('MIL', 'souvlaki pita is usually served with tzatziki, a yogurt sauce')),
        D('Baklava', '$7', 'filo, walnuts, honey syrup', A('TRE', 'the menu names walnuts'), A('WHE', 'filo is wheat pastry', 'BASIC'), Q('MIL', 'baklava is usually brushed with butter', 'FARE_MIL')),
        D('Loukoumades', '$7', 'fried dough puffs with honey', A('WHE', 'dough puffs are wheat', 'BASIC'), Q('EGG', 'dough often holds egg'), Q('SES', 'loukoumades are often sprinkled with sesame', 'FARE_SES')),
        D('Sesame Halva', '$5', 'sesame paste sweet', A('SES', 'the menu names sesame; halva is sesame paste', 'FARE_SES')),
        D('Grilled Octopus', '$16', 'octopus, olive oil, lemon', Q('SHE', 'octopus is a mollusc, not on the FDA crustacean list; many shellfish plans include it')),
    ]),
])

menu(id='M22', title='Wok & Fire Fusion', lang='en', font='trebuchet', bg='white', style='scan', heldout=False, sections=[
    ('From the wok', [
        D('Beef with Oyster Sauce', '$17', 'wok beef, broccoli, oyster sauce', Q('SHE', 'oyster is a mollusc, not on the FDA crustacean list; oyster sauce can hold shellfish extract'), Q('SOY', 'oyster sauce often holds soy', 'FARE_SOY'), Q('WHE', 'oyster sauce often holds wheat')),
        D('Caramel Pork', '$16', 'pork belly, fish sauce caramel, rice', A('FIS', 'the menu names fish sauce'), Q('SOY', 'caramel sauces often hold soy sauce', 'FARE_SOY')),
        D('Cashew Chicken', '$16', 'chicken, cashews, peppers, wok sauce', A('TRE', 'the menu names cashews'), Q('SOY', 'wok sauce usually holds soy sauce', 'FARE_SOY'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE')),
        D('Pad See Ew', '$14', 'wide rice noodles, egg, greens, soy sauce', A('EGG', 'the menu names egg'), *SOYS()),
        D('Tahini Noodles', '$13', 'wheat noodles, tahini dressing, cucumber', A('SES', 'the menu names tahini (sesame paste)', 'FARE_SES'), A('WHE', 'the menu names wheat noodles')),
    ]),
    ('Sides and starters', [
        D('Worcestershire Mushrooms', '$9', 'roasted mushrooms, Worcestershire glaze', Q('FIS', 'FARE lists Worcestershire sauce as a source of fish (anchovy)', 'FARE_FIS'), Q('WHE', 'Worcestershire sauce may use malt vinegar made from barley')),
        D('Steamed Bao', '$7', 'steamed bun, hoisin pork', A('WHE', 'the bun is wheat', 'BASIC'), Q('SOY', 'hoisin holds soy', 'FARE_SOY'), Q('SES', 'hoisin often holds sesame', 'FARE_SES'), Q('PEA', 'hoisin can hold peanut', 'FARE_PEA')),
        D('Mango Salad', '$8', 'green mango, herbs, lime dressing', Q('FIS', 'the dressing may hold fish sauce', 'FARE_FIS'), Q('PEA', 'Asian salads are often topped with peanuts', 'FARE_PEA')),
        D('Jasmine Rice', '$3', 'steamed rice'),
        D('Fortune Cookies', '$2', 'sweet cookies', A('WHE', 'cookies are wheat', 'BASIC'), Q('EGG', 'fortune cookies usually hold egg'), Q('SES', 'some fortune cookies are made with sesame', 'FARE_SES')),
    ]),
])

menu(id='M23', title='Sweet Ending Dessert Bar', lang='en', font='baskerville', bg='cream', style='photo', heldout=False, sections=[
    ('Cakes and pastry', [
        D('Stollen with Marzipan', '$8', 'spiced fruit bread, marzipan', A('TRE', 'marzipan is almond paste', 'FARE_TRE'), A('WHE', 'stollen is wheat bread', 'BASIC'), Q('PEA', 'FARE lists marzipan as a possible peanut source', 'FARE_PEA'), Q('EGG', 'marzipan and stollen often hold egg', 'FARE_EGG'), Q('MIL', 'stollen is made with butter', 'FARE_MIL')),
        D('Sticky Toffee Pudding', '$9', 'date sponge, toffee sauce', A('WHE', 'sponge is wheat', 'BASIC'), A('EGG', 'sponge holds egg', 'BASIC'), A('MIL', 'toffee sauce holds butter and cream', 'FARE_MIL')),
        D('Pavlova', '$9', 'meringue, whipped cream, berries', A('EGG', 'meringue is egg white', 'FARE_EGG'), A('MIL', 'the menu names whipped cream')),
        D('Panettone Slice', '$6', 'Italian sweet bread, candied fruit', A('WHE', 'panettone is wheat bread', 'BASIC'), A('EGG', 'panettone holds egg', 'BASIC'), Q('MIL', 'panettone holds butter', 'FARE_MIL'), Q('TRE', 'panettone variants include almond glaze')),
    ]),
    ('Cold and warm', [
        D('Kheer', '$7', 'rice pudding made with ghee and cardamom', A('MIL', 'the menu names ghee; rice pudding is made with milk', 'FARE_MIL')),
        D('Dark Chocolate Mousse', '$8', 'dark chocolate, whipped', A('EGG', 'chocolate mousse is usually made with egg', 'FARE_EGG'), Q('MIL', 'chocolate may hold milk', 'FARE_MIL')),
        D('Halva Sundae', '$9', 'vanilla ice cream, crumbled halva', A('SES', 'halva is sesame paste', 'FARE_SES'), A('MIL', 'ice cream is made with milk', 'BASIC')),
        D('Mango Sorbet', '$6', 'mango, sugar, water'),
        D('Praline Pecan Cluster', '$5', 'caramelized pecans', A('TRE', 'the menu names pecans; praline is a tree nut item', 'FARE_TRE'), Q('MIL', 'praline caramel often holds butter or cream')),
        D('Espresso', '$3', 'espresso'),
    ]),
])

menu(id='M24', title='Garden Grill', lang='en', font='georgia', bg='white', style='clean', heldout=True, sections=[
    ('Grill', [
        D('Grilled Chicken Breast', '$16', 'chicken, salt, pepper, lemon'),
        D('Grilled Steak', '$24', 'sirloin, salt, pepper'),
        D('Roasted Potatoes', '$5', 'potatoes, olive oil, salt, rosemary'),
        D('Steamed Rice', '$3', 'steamed rice'),
        D("Chef's Bowl of the Day", '$13', 'ask your server', *ALLQ()),
    ]),
    ('Sides and drinks', [
        D('Garden Salad', '$8', 'lettuce, tomato, cucumber, olive oil, lemon'),
        D('Steamed Broccoli', '$5', 'broccoli, salt'),
        D('Baked Sweet Potato', '$5', 'sweet potato, salt'),
        D('Sliced Fresh Fruit', '$6', 'apple, orange, grapes'),
        D('Sparkling Water', '$3', 'mineral water'),
    ]),
])
