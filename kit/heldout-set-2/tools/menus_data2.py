"""Menu content and allergen facts for HELD-OUT SET 2 (M25-M32). Pure data; uses the helpers of the frozen tools/menus_data.py.

Same rules as set 1: fact level A = Avoid (printed, or the dish is by definition made with it); Q = Ask the kitchen (hidden or
variable source). A profile's label: any A in its allergens -> Avoid; else any Q -> Ask the kitchen; else No listed allergen found.
New source ids (WP_*) are Wikipedia pages read through a page-fetch summary on 2026-11-14. GEN = general culinary knowledge, UNVERIFIED.
Written before any run; keys hashed in KEYS-HASHES-2.txt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import menus_data as M  # noqa: E402
from menus_data import A, Q, D, En, ALLQ  # noqa: E402

W = 'fetched 2026-11-14 (page-fetch summary)'
WP = 'https://en.wikipedia.org/wiki/'
SOURCES2 = {
    'WP_LAKSA': ('Wikipedia, Laksa: broths hold prawn paste or shrimp paste (belacan, hae ko); fish (often mackerel) in some types; boiled egg and fried tofu are toppings; coconut milk adds richness', WP + 'Laksa', W),
    'WP_PECEL': ('Wikipedia, Pecel: "a traditional Javanese salad with peanut sauce"; "The sauce is made of roasted (or fried) peanuts, tamarind, coconut sugar, and other spices"', WP + 'Pecel', W),
    'WP_KARYDO': ('Wikipedia, Karydopita: "A cake made primarily with walnuts and often partly soaked in syrup"; main ingredients walnut, flour, cinnamon', WP + 'Karydopita', W),
    'WP_NASI': ('Wikipedia, Nasi lemak: served with fried anchovies (ikan bilis), roasted peanuts, egg and sambal; the vegetarian version replaces "the dried anchovies and the shrimp paste for sambal", so normal sambal holds shrimp paste', WP + 'Nasi_lemak', W),
    'WP_ROTI': ('Wikipedia, Roti canai: dough "composed of fat (usually ghee), flour, and water"; some recipes add sweetened condensed milk', WP + 'Roti_canai', W),
    'WP_OKONO': ('Wikipedia, Okonomiyaki: batter of flour, yam, dashi or water and eggs; topped with okonomiyaki sauce (made with Worcestershire sauce), katsuobushi (bonito flakes) and Japanese mayonnaise', WP + 'Okonomiyaki', W),
    'WP_TAKO': ('Wikipedia, Takoyaki: "wheat flour-based batter", filled with octopus, "brushed with takoyaki sauce and mayonnaise" and topped with aonori and katsuobushi', WP + 'Takoyaki', W),
    'WP_DASHI': ('Wikipedia, Dashi: katsuobushi is preserved, fermented skipjack tuna and niboshi are small dried sardines; kombu and shiitake dashi are fish-free', WP + 'Dashi', W),
    'WP_YAKI': ('Wikipedia, Yakitori: tare glaze consists of "mirin, sake, soy sauce, and sugar"', WP + 'Yakitori', W),
    'WP_KARA': ('Wikipedia, Karaage: marinade "typically includes sake, soy sauce, ginger juice, and scallions"; pieces are dredged with a starch', WP + 'Karaage', W),
    'WP_NOGADA': ('Wikipedia, Chiles en nogada: "The cream sauce usually has milk, double cream, fresh cheese, sherry and walnut"; pecans may replace or add to walnuts', WP + 'Chiles_en_nogada', W),
    'WP_TARAMA': ('Wikipedia, Taramasalata: made from cured roe of cod, carp or grey mullet with a base of bread or potatoes, "or sometimes almonds"', WP + 'Taramasalata', W),
    'WP_SKORD': ('Wikipedia, Skordalia: garlic "in a base of potatoes, walnuts, almonds or liquid-soaked stale bread"', WP + 'Skordalia', W),
    'WP_TZAT': ('Wikipedia, Tzatziki: made of salted strained yogurt mixed with cucumbers, garlic, salt, olive oil', WP + 'Tzatziki', W),
    'WP_MOUSS': ('Wikipedia, Moussaka: the Greek version is "topped with a béchamel sauce"; the top layer is "a milk-based sauce thickened with egg (custard) or flour (béchamel)"', WP + 'Moussaka', W),
    'WP_BAKL': ('Wikipedia, Baklava: "filo pastry, filled with chopped nuts" (typically walnuts or pistachios), layers separated by melted butter', WP + 'Baklava', W),
    'WP_PUTT': ('Wikipedia, Spaghetti alla puttanesca: "typically made with tomatoes, olives, capers, anchovies"; the Neapolitan version is made without anchovies', WP + 'Spaghetti_alla_puttanesca', W),
    'WP_KFC': ('Wikipedia, Korean fried chicken: chicken coated with flour and fried; yangnyeom chicken is "coated in gochujang-based sweet and spicy sauce", ganjang chicken in soy sauce sauce', WP + 'Korean_fried_chicken', W),
    'WP_GOCHU': ('Wikipedia, Gochujang: made with meju (fermented soybean) powder, glutinous rice and barley malt powder', WP + 'Gochujang', W),
    'WP_SUJ': ('Wikipedia, Sujeonggwa: cinnamon, sugar, water and ginger punch, "often served with gotgam (dried persimmon) and garnished with pine nuts"', WP + 'Sujeonggwa', W),
    'WP_FINAN': ('Wikipedia, Financier (cake): main ingredients are beurre noisette and "almond flour or ground almonds"; also egg whites, flour and powdered sugar', WP + 'Financier_(cake)', W),
    'WP_MACA': ('Wikipedia, Macaron: "made with egg white, icing sugar, granulated sugar, almond meal"; filled with ganache, buttercream or jam', WP + 'Macaron', W),
    'WP_QUICHE': ('Wikipedia, Quiche Lorraine: "a filling of cream, eggs, and bacon, in an open pastry case"; shortcrust or puff pastry', WP + 'Quiche_Lorraine', W),
    'WP_HUSH': ('Wikipedia, Hush puppy: typical recipes use "cornmeal, wheat flour, eggs, salt, baking soda, milk or buttermilk, and water"; served with fried seafood', WP + 'Hush_puppy', W),
    'WP_BRIOCHE': ('Wikipedia, Brioche: "flour, eggs, butter, liquid (milk, water, cream...)"; "commonly used for hamburgers"', WP + 'Brioche', W),
    'FARE_SES2': ('FARE sesame page, "Foods That May Contain Sesame": baked goods (bagels, bread, breadsticks, hamburger buns and rolls); dressings, gravies, marinades and sauces; dipping sauces',
                  'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/sesame', W),
}

MENUS2 = []


def menu(**kw):
    MENUS2.append(kw)


# ---------------------------------------------------------------- M25 Italian (en, clean, clean and variable dish)
menu(id='M25', title='Osteria Lunetta', lang='en', font='gill', bg='white', style='clean', heldout=True, sections=[
    ('Antipasti and pasta', [
        D('Bruschetta al Pomodoro', '$9', 'grilled country bread, tomato, basil, olive oil', A('WHE', 'bread is wheat', 'BASIC')),
        D('Arancini', '$10', 'fried risotto balls, mozzarella, crisp breadcrumb crust',
          A('MIL', 'the menu names mozzarella'), A('WHE', 'the menu names a breadcrumb crust'), Q('EGG', 'breadcrumb coatings are usually set with egg wash')),
        D('Spaghetti Puttanesca', '$16', 'tomato, olives, capers, garlic, chili',
          Q('FIS', 'puttanesca is typically made with anchovies, which the menu does not print', 'WP_PUTT'), A('WHE', 'spaghetti is wheat', 'BASIC')),
        D('Spaghetti Carbonara', '$17', 'guanciale, pecorino, black pepper',
          A('MIL', 'pecorino is a cheese'), A('EGG', 'carbonara sauce is made with eggs', 'BASIC'), A('WHE', 'spaghetti is wheat', 'BASIC')),
        D('Gnocchi al Gorgonzola', '$17', 'potato gnocchi, gorgonzola cream',
          A('MIL', 'the menu names gorgonzola cream'), A('WHE', 'gnocchi dough holds flour', 'BASIC'), Q('EGG', 'gnocchi dough often holds egg')),
    ]),
    ('Specials, mains and sweets', [
        D("Chef's Fresh Pasta Special", '$18', 'changes with the market, ask your server', *ALLQ()),
        D('Veal Milanese', '$24', 'pounded veal cutlet, lemon, arugula',
          A('WHE', 'a Milanese cutlet is breaded in breadcrumbs', 'BASIC'), A('EGG', 'the breading is set with egg', 'BASIC'), Q('MIL', 'the cutlet is traditionally fried in butter')),
        D('Pan-Seared Sea Bream', '$26', 'whole sea bream, lemon, olive oil', A('FIS', 'the menu names sea bream')),
        D('Grilled Zucchini', '$8', 'zucchini, olive oil, mint, sea salt'),
        D('Cannoli Siciliani', '$8', 'crisp shell, sweet ricotta, chocolate chips',
          A('MIL', 'the menu names ricotta'), A('WHE', 'the shell is wheat', 'BASIC'), Q('TRE', 'cannoli are often finished with chopped pistachios'), Q('EGG', 'cannoli shell dough often holds egg')),
        D('Lemon Sorbetto', '$6', 'lemon, sugar, water'),
    ]),
])

# ---------------------------------------------------------------- M26 American BBQ (en, photo): burgers, buns, batters, BBQ sauce
menu(id='M26', title='Smokestack Pit & Grill', lang='en', font='rockwell', bg='kraft', style='photo', heldout=True, sections=[
    ('From the pit', [
        D('Brisket Plate', '$22', 'smoked beef brisket, pickles, white bread, house BBQ sauce',
          A('WHE', 'the menu names white bread', 'BASIC'), Q('FIS', 'barbecue sauce can hold Worcestershire sauce, which holds anchovy', 'FARE_FIS'), Q('SES', 'bread and rolls can hold sesame', 'FARE_SES2')),
        D('Baby Back Ribs', '$26', 'half rack, dry rub, brushed with our sticky glaze',
          Q('FIS', 'barbecue glazes can hold Worcestershire sauce, which holds anchovy', 'FARE_FIS'), Q('SOY', 'barbecue glazes often hold soy sauce')),
        D('Smoked Turkey Leg', '$14', 'turkey leg, salt, pepper, paprika'),
        D('Smash Burger', '$15', 'two patties, American cheese, pickles, special sauce',
          A('MIL', 'the menu names cheese'), Q('WHE', 'the bun is not printed; burger buns are usually wheat', 'FARE_WHE'), Q('SES', 'hamburger buns can hold sesame', 'FARE_SES2'),
          Q('EGG', 'special sauce is usually mayonnaise based, and mayonnaise holds egg', 'FARE_EGG')),
        D('Bacon BBQ Burger', '$17', 'beef patty, bacon, cheddar, onion ring, brioche bun, BBQ sauce',
          A('MIL', 'the menu names cheddar'), A('WHE', 'the menu names a brioche bun and an onion ring'), Q('EGG', 'brioche is made with eggs', 'WP_BRIOCHE'),
          Q('FIS', 'barbecue sauce can hold Worcestershire sauce, which holds anchovy', 'FARE_FIS'), Q('SES', 'hamburger buns can hold sesame', 'FARE_SES2')),
        D('Fried Catfish Basket', '$18', 'cornmeal-crusted catfish, hush puppies, tartar sauce',
          A('FIS', 'the menu names catfish'), Q('WHE', 'hush puppies hold wheat flour', 'WP_HUSH'), Q('EGG', 'hush puppies hold eggs and tartar sauce is mayonnaise based', 'WP_HUSH'),
          Q('MIL', 'hush puppies hold milk or buttermilk', 'WP_HUSH')),
        D("Pitmaster's Special", '$24', 'ask your server what came off the smoker today', *ALLQ()),
    ]),
    ('Sides and sweets', [
        D('Onion Rings', '$8', 'thick-cut, beer-battered, fried',
          A('WHE', 'batter-fried foods are wheat sources', 'FARE_WHE'), Q('EGG', 'batters often hold egg', 'FARE_EGG'), Q('MIL', 'batters often use buttermilk or milk')),
        D('Mac and Cheese', '$9', 'elbow pasta, cheddar sauce, breadcrumb top', A('MIL', 'the menu names cheddar sauce'), A('WHE', 'pasta and breadcrumbs are wheat', 'BASIC')),
        D('Creamy Coleslaw', '$5', 'cabbage, carrot, house dressing',
          Q('EGG', 'creamy slaw dressing is usually mayonnaise, which holds egg', 'FARE_EGG'), Q('MIL', 'creamy slaw dressing may hold buttermilk or cream')),
        D('Pecan Pie', '$8', 'pecans, butter crust, whipped cream',
          A('TRE', 'the menu names pecans'), A('MIL', 'the menu names butter and whipped cream'), A('WHE', 'pie crust is wheat', 'BASIC'), A('EGG', 'pecan pie filling is set with eggs', 'BASIC')),
        D('Peanut Butter Shake', '$7', 'peanut butter, vanilla ice cream, milk',
          A('PEA', 'the menu names peanut butter'), A('MIL', 'the menu names milk and ice cream'), Q('EGG', 'ice cream can hold egg')),
    ]),
])

# ---------------------------------------------------------------- M27 Indonesian / Malaysian (en with Malay words, glare)
menu(id='M27', title='Kedai Makan Pelangi', lang='en', font='trebuchet', bg='cream', style='glare', heldout=True, sections=[
    ('Rice and noodles', [
        D('Nasi Lemak', '$12', 'coconut rice, fried egg, cucumber, sambal, crispy ikan bilis, kacang',
          A('EGG', 'the menu names fried egg'), A('FIS', 'ikan bilis means dried anchovies', 'WP_NASI'), A('PEA', 'kacang means peanuts; nasi lemak comes with roasted peanuts', 'WP_NASI'),
          Q('SHE', 'sambal for nasi lemak is normally made with shrimp paste', 'WP_NASI')),
        D('Mee Goreng Mamak', '$13', 'fried yellow noodles, prawns, tofu, egg, tomato sauce',
          A('SHE', 'the menu names prawns'), A('SOY', 'the menu names tofu', 'FARE_SOY'), A('EGG', 'the menu names egg'), A('WHE', 'yellow noodles are wheat', 'BASIC'),
          Q('FIS', 'Indonesian and Malaysian dishes can hold hidden fish sauce or fish', 'FARE_FIS'), Q('PEA', 'FARE lists Indonesian restaurant food as a peanut source', 'FARE_PEA')),
        D('Char Kway Teow', '$13', 'flat rice noodles, cockles, egg, bean sprouts, chives, dark soy sauce',
          A('EGG', 'the menu names egg'), *[A('SOY', 'the menu names soy sauce'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE')],
          Q('SHE', 'cockles are molluscs, not on the FDA crustacean list; many shellfish plans include them')),
        D('Laksa Lemak', '$14', 'rice noodles in spicy coconut broth, tofu puffs, boiled egg, bean sprouts',
          A('SOY', 'the menu names tofu puffs', 'FARE_SOY'), A('EGG', 'the menu names boiled egg'),
          Q('SHE', 'laksa broth is made with prawn or shrimp paste', 'WP_LAKSA'), Q('FIS', 'laksa broth can hold flaked fish such as mackerel', 'WP_LAKSA')),
        D('Nasi Putih', '$3', 'steamed white rice'),
    ]),
    ('Plates and sweets', [
        D('Pecel Sayur', '$11', 'blanched vegetables, fried tofu, tempeh, boiled egg, house dressing',
          A('SOY', 'the menu names tofu and tempeh', 'FARE_SOY'), A('EGG', 'the menu names boiled egg'),
          A('PEA', 'pecel is a salad of vegetables in peanut sauce, made of roasted peanuts', 'WP_PECEL')),
        D('Ayam Penyet', '$14', 'smashed fried chicken, sambal, tempeh, cucumber',
          A('SOY', 'the menu names tempeh', 'FARE_SOY'), Q('SHE', 'sambal is normally made with shrimp paste', 'WP_NASI'), Q('WHE', 'fried chicken is usually coated in flour'),
          Q('PEA', 'FARE lists Indonesian restaurant food as a peanut source', 'FARE_PEA')),
        D('Soto Ayam', '$12', 'turmeric chicken soup, glass noodles, boiled egg, celery',
          A('EGG', 'the menu names boiled egg'), Q('SOY', 'sweet soy sauce is a common seasoning', 'FARE_SOY'), Q('SHE', 'soto is often topped with prawn cracker powder')),
        D('Tempe Mendoan', '$7', 'thin battered fried tempeh, sweet chili dip',
          A('SOY', 'the menu names tempeh', 'FARE_SOY'), A('WHE', 'batter-fried foods are wheat sources', 'FARE_WHE'), Q('EGG', 'batters often hold egg', 'FARE_EGG'),
          Q('PEA', 'FARE lists chili sauce and Indonesian food as peanut sources; sweet chili dips can hold ground peanut', 'FARE_PEA')),
        D('Es Cendol', '$6', 'shaved ice, coconut milk, green rice-flour jelly, palm sugar, red beans'),
        D('Kuih of the Day', '$5', 'ask at the counter', *ALLQ()),
    ]),
])

# ---------------------------------------------------------------- M28 Korean (ko, clean)
menu(id='M28', title='한옥정 식당', lang='ko', font='unicode', bg='cream', style='clean', heldout=True, sections=[
    ('찌개, 밥과 오늘의 메뉴', [
        D('순두부찌개', '₩11,000', '순두부, 바지락, 계란, 고춧가루',
          A('SOY', 'the menu names soft tofu (순두부)', 'FARE_SOY'), A('EGG', 'the menu names egg (계란)'),
          Q('SHE', 'clams (바지락) are molluscs, not on the FDA crustacean list; many shellfish plans include them'), Q('FIS', 'Korean stews are often made with anchovy stock', 'FARE_FIS'),
          en='Soft tofu stew'),
        D('김치볶음밥', '₩10,000', '김치, 밥, 계란 프라이, 참기름',
          A('EGG', 'the menu names fried egg (계란 프라이)'), A('SES', 'the menu names sesame oil (참기름)'),
          Q('FIS', 'kimchi is often made with fish sauce', 'FARE_FIS'), Q('SHE', 'kimchi is often made with salted shrimp'), en='Kimchi fried rice'),
        D('냉면', '₩11,000', '메밀국수, 차가운 육수, 오이, 삶은 계란, 배',
          A('EGG', 'the menu names boiled egg (삶은 계란)'), Q('WHE', 'buckwheat noodles are usually blended with wheat flour'), Q('SES', 'cold noodle dishes are often finished with sesame', 'FARE_SES'),
          en='Cold buckwheat noodles'),
        D('갈비탕', '₩15,000', '소갈비, 당면, 대파, 무',
          Q('SOY', 'beef soups are seasoned with soy sauce', 'FARE_SOY'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE'), en='Short rib soup'),
        D('오늘의 반찬 세트', '₩8,000', '그날 준비한 반찬입니다. 직원에게 문의하세요', *ALLQ(), en='Side dishes of the day'),
    ]),
    ('구이, 안주와 후식', [
        D('삼겹살', '₩16,000', '삼겹살, 쌈 채소, 쌈장',
          Q('SOY', 'ssamjang is made with fermented soybean paste and gochujang', 'WP_GOCHU'), en='Grilled pork belly'),
        D('양념치킨', '₩20,000', '바삭한 튀김옷, 매콤달콤 양념 소스',
          A('WHE', 'Korean fried chicken is coated with flour', 'WP_KFC'), Q('SOY', 'yangnyeom sauce is gochujang based; gochujang holds fermented soybean', 'WP_GOCHU'),
          Q('SES', 'sesame seeds are a common garnish', 'FARE_SES'), Q('EGG', 'the coating batter often holds egg'), en='Sweet and spicy fried chicken'),
        D('김치전', '₩10,000', '김치, 부침가루, 오징어',
          A('WHE', 'the menu names pancake flour (부침가루)'), Q('EGG', 'pancake batter often holds egg'), Q('SHE', 'squid (오징어) is a mollusc, not on the FDA crustacean list; many shellfish plans include it'),
          Q('FIS', 'kimchi is often made with fish sauce', 'FARE_FIS'), en='Kimchi pancake'),
        D('고기만두', '₩9,000', '돼지고기 만두 여섯 개, 간장 소스',
          A('SOY', 'the menu names soy sauce (간장)'), Q('WHE', 'the dumpling wrapper is wheat; soy sauce sometimes contains wheat', 'FARE_WHE'),
          Q('SES', 'dumpling filling and sauce often hold sesame oil', 'FARE_SES'), en='Pork dumplings'),
        D('수정과', '₩5,000', '계피, 생강, 곶감',
          Q('TRE', 'sujeonggwa is often garnished with pine nuts', 'WP_SUJ'), en='Cinnamon punch'),
        D('군고구마', '₩5,000', '구운 고구마', en='Roasted sweet potato'),
    ]),
])

# ---------------------------------------------------------------- M29 Mexican (en, blur)
menu(id='M29', title='Cocina Azul Marina', lang='en', font='futura', bg='white', style='blur', heldout=True, sections=[
    ('Platos fuertes', [
        D('Chiles en Nogada', '$22', 'poblano chile stuffed with picadillo, nogada sauce, pomegranate',
          A('TRE', 'nogada sauce is made with walnut', 'WP_NOGADA'), A('MIL', 'nogada sauce is made with milk, cream and fresh cheese', 'WP_NOGADA')),
        D('Fish Tacos Baja', '$15', 'beer-battered cod, cabbage slaw, chipotle crema, flour tortilla',
          A('FIS', 'the menu names cod'), A('WHE', 'the menu names beer batter and a flour tortilla'), A('MIL', 'the menu names crema'),
          Q('EGG', 'batter and slaw dressing can hold egg', 'FARE_EGG')),
        D('Tacos al Pastor', '$13', 'marinated pork, pineapple, onion, cilantro, corn tortillas'),
        D('Camarones a la Diabla', '$19', 'shrimp in a hot red chile sauce, lime, rice', A('SHE', 'the menu names shrimp')),
        D('Pozole Rojo', '$14', 'hominy, pork, red chile broth, radish, shredded cabbage'),
        D('Tamales Verdes', '$11', 'steamed corn masa, chicken, tomatillo salsa'),
        D('Ceviche of the Day', '$16', 'ask your server what the kitchen has today', *ALLQ()),
    ]),
    ('Antojitos y dulces', [
        D('Guacamole', '$9', 'avocado, lime, onion, cilantro, tortilla chips'),
        D('Chilaquiles Verdes', '$13', 'fried tortilla chips in green salsa, fried egg, queso fresco', A('EGG', 'the menu names fried egg'), A('MIL', 'the menu names queso fresco')),
        D('Buñuelos con Piloncillo', '$8', 'crisp fried dough fritters, cinnamon, piloncillo syrup',
          A('WHE', 'fritter dough is wheat', 'BASIC'), Q('EGG', 'fritter dough often holds egg')),
        D('Agua de Jamaica', '$4', 'chilled hibiscus flower drink, lime'),
    ]),
])

# ---------------------------------------------------------------- M30 Greek (en, clean)
menu(id='M30', title='Taverna Meltemi', lang='en', font='cochin', bg='cream', style='clean', heldout=True, sections=[
    ('Mezedes', [
        D('Taramosalata', '$8', 'whipped spread, lemon, olive oil, warm pita',
          A('FIS', 'taramosalata is made from cured fish roe', 'WP_TARAMA'), A('WHE', 'pita is wheat', 'BASIC'), Q('TRE', 'the starchy base is sometimes almonds', 'WP_TARAMA')),
        D('Skordalia', '$7', 'garlic dip, olive oil, red wine vinegar',
          Q('TRE', 'skordalia is often made with walnuts or almonds', 'WP_SKORD'), Q('WHE', 'skordalia is often made with stale bread', 'WP_SKORD')),
        D('Tzatziki', '$7', 'cucumber, garlic, olive oil, warm pita',
          A('MIL', 'tzatziki is made of strained yogurt', 'WP_TZAT'), A('WHE', 'pita is wheat', 'BASIC')),
        D('Gigantes', '$9', 'baked giant beans, tomato, dill, olive oil'),
        D('Horiatiki', '$12', 'tomato, cucumber, olives, red onion, feta', A('MIL', 'the menu names feta')),
        D('Kolokithokeftedes', '$10', 'zucchini fritters, feta, mint',
          A('MIL', 'the menu names feta'), Q('WHE', 'fritters are bound with flour'), Q('EGG', 'fritters are usually bound with egg')),
    ]),
    ('Mains and sweets', [
        D('Pastitsio', '$17', 'baked tubular pasta, spiced beef, béchamel',
          A('WHE', 'tubular pasta is wheat', 'BASIC'), A('MIL', 'béchamel is a milk-based sauce', 'WP_MOUSS'), Q('EGG', 'the béchamel topping may be set with egg', 'WP_MOUSS')),
        D('Lamb Kleftiko', '$24', 'slow-baked lamb, potatoes, lemon, oregano, baked in parchment'),
        D('Garides Saganaki', '$19', 'garides baked in tomato sauce, ouzo, feta',
          A('SHE', 'garides means shrimp', 'BASIC'), A('MIL', 'the menu names feta')),
        D('Fish of the Day', '$26', 'ask your server which fish came in today and how it is cooked',
          A('FIS', 'the menu names fish'), Q('SHE', 'the preparation is not stated'), Q('MIL', 'fish may be cooked in butter'), Q('WHE', 'fish may be dusted with flour'), Q('SOY', 'the preparation is not stated', 'PRINTED')),
        D('Galaktoboureko', '$8', 'crisp filo, vanilla semolina custard, lemon syrup',
          A('WHE', 'filo and semolina are wheat', 'BASIC'), A('MIL', 'the custard is made with milk', 'FARE_MIL'), A('EGG', 'custard is made with egg', 'BASIC')),
        D('Karydopita', '$7', 'spiced syrup cake, cinnamon, vanilla ice cream',
          A('TRE', 'karydopita is a cake made primarily with walnuts', 'WP_KARYDO'), A('WHE', 'the cake holds flour', 'WP_KARYDO'), A('MIL', 'the menu names ice cream', 'BASIC'), Q('EGG', 'cakes and ice cream can hold egg', 'FARE_EGG')),
    ]),
])

# ---------------------------------------------------------------- M31 Japanese izakaya (ja, photo)
menu(id='M31', title='居酒屋 酔月', lang='ja', font='unicode', bg='kraft', style='photo', heldout=True, sections=[
    ('焼き物と揚げ物', [
        D('焼き鳥盛り合わせ', '¥980', '鶏もも、ねぎま、つくね、特製たれ',
          Q('SOY', 'the tare glaze is made with soy sauce', 'WP_YAKI'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE'), Q('EGG', 'chicken meatballs (つくね) are often bound with egg'),
          en='Assorted yakitori skewers'),
        D('鶏の唐揚げ', '¥680', '鶏もも肉の唐揚げ、レモン',
          Q('SOY', 'karaage marinade typically includes soy sauce', 'WP_KARA'), Q('WHE', 'soy sauce sometimes contains wheat, and the coating may be flour', 'FARE_WHE'), en='Fried chicken'),
        D('たこ焼き', '¥650', '八個入り、ソース、マヨネーズ、かつお節',
          A('FIS', 'the menu names bonito flakes (かつお節)', 'WP_TAKO'), A('EGG', 'the menu names mayonnaise (マヨネーズ)', 'FARE_EGG'), A('WHE', 'takoyaki batter is wheat flour based', 'WP_TAKO'),
          Q('SHE', 'takoyaki holds octopus, a mollusc, not on the FDA crustacean list; many shellfish plans include it'),
          Q('SOY', 'takoyaki sauce is a Worcestershire-style sauce, and soy is common in such sauces', 'FARE_SOY'), en='Takoyaki octopus balls'),
        D('お好み焼き', '¥850', 'キャベツ、豚バラ、ソース',
          A('WHE', 'okonomiyaki batter is made with flour', 'WP_OKONO'), A('EGG', 'okonomiyaki batter is made with eggs', 'WP_OKONO'),
          Q('FIS', 'okonomiyaki sauce is made with Worcestershire sauce and the dish is usually topped with bonito flakes', 'WP_OKONO'), Q('SOY', 'okonomiyaki sauce commonly holds soy', 'FARE_SOY'),
          en='Savory cabbage pancake'),
        D('焼きおにぎり', '¥400', '醤油、ご飯',
          A('SOY', 'the menu names soy sauce (醤油)'), Q('WHE', 'soy sauce sometimes contains wheat', 'FARE_WHE'), en='Grilled rice ball'),
    ]),
    ('おつまみ', [
        D('刺身盛り合わせ', '¥1,480', 'まぐろ、サーモン、白身魚、わさび', A('FIS', 'the menu names tuna and salmon'), en='Assorted sashimi'),
        D('だし巻き卵', '¥600', 'だしを使った卵焼き',
          A('EGG', 'the dish is a rolled omelet (卵焼き)'), Q('FIS', 'dashi is usually made with katsuobushi (bonito) or dried sardines', 'WP_DASHI'), en='Dashi rolled omelet'),
        D('ポテトサラダ', '¥450', 'じゃがいも、きゅうり、ハム、マヨネーズ',
          A('EGG', 'the menu names mayonnaise (マヨネーズ)', 'FARE_EGG'), en='Potato salad'),
        D('ごま豆腐', '¥480', '胡麻豆腐、わさび', A('SES', 'the menu names sesame (胡麻)'), en='Sesame tofu'),
        D('きゅうりの浅漬け', '¥350', 'きゅうり、塩、昆布', en='Light cucumber pickles'),
        D('本日のおすすめ', '¥700', '黒板の本日のメニューは店員におたずねください', *ALLQ(), en="Today's special"),
    ]),
])

# ---------------------------------------------------------------- M32 French bakery (en, scan)
menu(id='M32', title='Boulangerie Petit Matin', lang='en', font='baskerville', bg='cream', style='scan', heldout=True, sections=[
    ('Viennoiserie, bread and savoury', [
        D('Croissant au Beurre', '$4', 'all-butter laminated pastry', A('MIL', 'the menu names butter'), A('WHE', 'pastry dough is wheat', 'BASIC')),
        D('Pain au Chocolat', '$5', 'laminated pastry, dark chocolate',
          A('WHE', 'pastry dough is wheat', 'BASIC'), Q('MIL', 'laminated pastry is made with butter; chocolate and baked goods may hold milk', 'FARE_MIL')),
        D('Baguette Tradition', '$3', 'crisp crust, open crumb', A('WHE', 'bread flour is wheat', 'BASIC'), Q('SES', 'bread and rolls can hold sesame', 'FARE_SES2')),
        D('Pain aux Noix', '$6', 'country loaf with noix and raisins', A('TRE', 'noix means walnuts'), A('WHE', 'bread is wheat', 'BASIC')),
        D('Quiche Poireaux-Chèvre', '$9', 'leek, goat cheese, savoury custard, shortcrust',
          A('EGG', 'the menu names custard; quiche filling is cream and eggs', 'WP_QUICHE'), A('MIL', 'the menu names goat cheese; quiche filling is made with cream', 'WP_QUICHE'), A('WHE', 'shortcrust pastry is wheat', 'WP_QUICHE')),
        D('Velouté de Potimarron', '$10', 'roasted pumpkin soup, croutons, chives', A('WHE', 'the menu names croutons', 'BASIC'), Q('MIL', 'velouté soups are often finished with cream or butter')),
    ]),
    ('Patisserie and drinks', [
        D('Financier', '$5', 'small golden cake with a crisp edge',
          A('TRE', 'a financier is made with almond flour', 'WP_FINAN'), A('MIL', 'a financier is made with browned butter', 'WP_FINAN'),
          A('EGG', 'a financier is made with egg whites', 'WP_FINAN'), A('WHE', 'a financier holds flour', 'WP_FINAN')),
        D('Macarons Box of Six', '$12', 'assorted flavours, ganache filling',
          A('TRE', 'macaron shells are made with almond meal', 'WP_MACA'), A('EGG', 'macaron shells are made with egg white', 'WP_MACA'), Q('MIL', 'ganache or buttercream filling can hold cream or butter', 'WP_MACA')),
        D('Éclair au Café', '$6', 'choux pastry, coffee cream',
          A('MIL', 'the menu names cream'), A('WHE', 'choux pastry is wheat', 'BASIC'), A('EGG', 'choux pastry is made with eggs', 'BASIC')),
        D('Tarte du Jour', '$7', "baked this morning, ask for today's flavour", *ALLQ()),
        D('Compote de Pommes', '$5', 'stewed apples, cinnamon'),
        D("Jus d'Orange Pressé", '$5', 'freshly pressed orange juice'),
    ]),
])

M.SOURCES.update(SOURCES2)
