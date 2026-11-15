"""Menu content and allergen facts for HELD-OUT SET 3 (M33-M40). Pure data plus one rule engine; uses the helpers of the frozen tools/menus_data.py.

Same label rule as sets 1 and 2: fact level A = Avoid (the menu prints the allergen, or it is a basic ingredient of the named dish);
Q = Ask the kitchen (a public source says the dish or a part of it can hold it, or the menu does not say what is in it).
Strictest fact wins per list.

NEW IN SET 3 (key-quality rule): every FARE "may contain" list item is a RULE (RULES_Q below) applied by code to EVERY dish whose
text matches it, so one source rule gives one label for every dish it covers. A printed allergen word or a basic ingredient
(RULES_A) gives Avoid. Hand-written facts are only for dish-specific sources (Wikipedia pages, WP_*), basic ingredients that need a
dish-specific reason, and the "special / of the day" dishes. check_rules() fails the build if any dish text matches a rule and has no fact
for that allergen. Matching runs over the printed name, subtitle, description, the English gloss and `kw`, which is a plain English
translation of the printed line (needed for zh, vi and es menus; empty on English menus).
Written before any run; keys hashed in KEYS-HASHES.txt.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import menus_data as M  # noqa: E402
from menus_data import A, Q, En, ALLQ  # noqa: E402
import menus_data as _M  # noqa: E402

W = 'fetched 2026-11-14 (page-fetch summary)'
WP = 'https://en.wikipedia.org/wiki/'
FARE = 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/'
SOURCES3 = {
    'FARE_SES3': ('FARE sesame page, full "Foods That May Contain Sesame" list: Asian cuisine; baked goods (bagels, bread, breadsticks, hamburger buns and rolls); bread crumbs; cereals (granola, muesli); chips (bagel, pita, tortilla); crackers; dipping sauces (baba ghanoush, hummus, tahini sauce); dressings, gravies, marinades and sauces; falafel; hummus; flavored rice, noodles, risotto, shish kebabs, stews and stir fry; goma-dofu; herbs and herbal drinks; margarine; pasteli; processed meats and sausages; protein bars; snack foods (pretzels, candy, halvah, rice cakes); soups; sushi; tempeh; Turkish cake; vegetarian burgers', FARE + 'sesame', W),
    'FARE_SOY3': ('FARE soy page, named and unexpected sources: soy sauce, miso, tofu, tempeh, edamame, tamari, shoyu, natto, soy flour; grains prepared with soy (cereals, breads, chips, crackers, pasta, rice, tortillas); vegetable broth; baked goods, canned broths and soups, canned tuna and meat, cereals, cookies, crackers, dairy products (ice cream, yogurt), processed meats, sauces, sausages; Asian cuisine (Chinese, Indian, Indonesian, Thai, Vietnamese)', FARE + 'soy', W),
    'FARE_WHE3': ('FARE wheat page, hidden sources: soy sauce, surimi, imitation crab meat, batter-fried foods, breaded foods, baked goods, beer and ale, candy, crackers, hot dogs, ice cream, marinara sauce, processed meats, salad dressings, sauces, sausages, soups, breakfast cereals; bread crumbs, couscous, bulgur, semolina, flour, pasta are wheat', FARE + 'wheat', W),
    'FARE_EGG3': ('FARE egg page, named and hidden sources: mayonnaise, meringue, hollandaise, souffle, salad dressings, marzipan, marshmallows, nougat, eggnog, surimi; most commercial cooked pasta; baked goods; breads (may be coated with an egg wash); breakfast foods (pancakes, waffles); cake fillings (buttercream, frosting, mousse); ice cream, custard, sorbet; pretzels; tortillas; specialty coffee drinks (egg foam)', FARE + 'egg', W),
    'FARE_MIL3': ('FARE milk page: butter, buttermilk, cheese, cream, custard, ghee, pudding, sour cream, whey, yogurt; hidden sources: baked goods and desserts, breakfast foods (cereals, pancakes, waffles), caramel candies, chocolate, luncheon meat, hot dogs and sausages, margarine, nougat, pantry staples (breads, pasta, tortillas), shellfish (sometimes dipped in milk), sherbet, snack foods (chips, crackers, pretzels), tuna fish, specialty beverages (smoothies, lattes), butter on grilled steaks', FARE + 'milk', W),
    'FARE_FIS3': ('FARE fish page: fish flavoring, fish gelatin, fish oil, fish sticks; unexpected sources: barbecue sauce, bouillabaisse, Caesar salad and dressing, caponata, surimi (imitation fish or shellfish), Worcestershire sauce, kimchi made with fish sauce; African, Chinese, Indonesian, Thai and Vietnamese cuisines', FARE + 'fish', W),
    'FARE_PEA3': ('FARE peanut page, hidden sources: African, Asian and Mexican restaurant food; baked goods, pies, cookies, pudding, hot chocolate, candy, chocolate, ice creams, pancakes, granola, trail mix, marzipan, nougat, chili, egg rolls, enchilada sauce, glazes and marinades, sauces (chili sauce, hot sauce, pesto, gravy, mole sauce, salad dressing), specialty pizzas, vegetarian meat substitutes', FARE + 'peanut', W),
    'FARE_TRE3': ('FARE tree nut page, hidden sources: pesto, marzipan/almond paste, gianduja, praline, nut milks, nut butters, nut oils, cereals, crackers, cookies, candy, chocolates, confections, energy bars, flavored coffee, frozen desserts, marinades, barbecue sauces, some cold cuts such as mortadella; coconut is not usually restricted', FARE + 'tree-nut', W),
    'FARE_SHE3': ('FARE shellfish page: bouillabaisse, cuttlefish ink, glucosamine, fish stock, seafood flavoring (crab or clam extract), fish stock or fish sauce sometimes made from krill, surimi', FARE + 'shellfish', W),
    'WP_PBUN': ('Wikipedia, Pineapple bun: topping is a cookie-style dough made with "sugar, eggs, flour, and lard" over a sweet bread dough; the buttered variant has "a slice of butter stuffed inside"', WP + 'Pineapple_bun', W),
    'WP_HKMT': ('Wikipedia, Hong Kong-style milk tea: Ceylon black tea with "evaporated milk instead of fresh milk"; a variant uses sweetened condensed milk', WP + 'Hong_Kong-style_milk_tea', W),
    'WP_NUOC': ('Wikipedia, Nuoc cham: the best-known version is a dipping sauce "made from fish sauce" with lime, sugar, garlic and chili; vegetarian versions use Maggi or soy sauce; the peanut sauce served with gỏi cuốn is a separate hoisin-based sauce', WP + 'N%C6%B0%E1%BB%9Bc_ch%E1%BA%A5m', W),
    'WP_BXEO': ('Wikipedia, Banh xeo: batter of rice flour, water and turmeric (coconut milk in Mekong Delta versions); fillings prawns, pork, green onions, bean sprouts; served with a sweet and sour garlic fish sauce', WP + 'B%C3%A1nh_x%C3%A8o', W),
    'WP_KSOI': ('Wikipedia, Khao soi: "deep-fried crispy egg noodles and boiled egg noodles" in a coconut milk curry; pickled mustard greens, shallots, lime and fried chili as toppings', WP + 'Khao_soi', W),
    'WP_GYANG': ('Wikipedia, Gai yang: marinade built on "fish sauce, garlic, turmeric, coriander root (cilantro), and white pepper"; variations may add soy sauce, hoisin or palm sugar', WP + 'Gai_yang', W),
    'WP_SAIUA': ('Wikipedia, Sai ua: Northern Thai sausage of chopped pork with lemongrass, galangal, kaffir lime leaves, shallots, chilies, garlic, salt and fish sauce', WP + 'Sai_ua', W),
    'WP_DMAKH': ('Wikipedia, Dal makhani: urad dal and kidney beans; the dish "includes butter and cream", ghee for tempering; yogurt optional garnish', WP + 'Dal_makhani', W),
    'WP_KORMA': ('Wikipedia, Korma: yogurt, ghee, spices; cream and "almonds, cashews or other nuts" in some versions; coconut milk in some', WP + 'Korma', W),
    'WP_AJI': ('Wikipedia, Aji de gallina: thickened with "bread soaked in milk or evaporated milk", Parmesan-style cheese and "ground nuts such as pecans or walnuts"; garnished with hard-boiled egg', WP + 'Aj%C3%AD_de_gallina', W),
    'WP_HUANC': ('Wikipedia, Papa a la huancaina: sauce of queso fresco, aji amarillo, evaporated milk, onion, garlic and oil; garnished with olives, corn and hard-boiled egg; the crackers and toasted peanuts belong to the related ocopa sauce', WP + 'Papa_a_la_huanca%C3%ADna', W),
    'WP_LOMO': ('Wikipedia, Lomo saltado: main ingredients beef steak, onions, tomatoes, french fries, soy sauce, rice, vinegar; beef is marinated with vinegar, soy sauce and spices and stir-fried', WP + 'Lomo_saltado', W),
    'WP_ANTI': ('Wikipedia, Anticucho: marinade of vinegar and spices (cumin, aji pepper, garlic), basting sauce may add aji panca and beer; some regional versions come with a peanut-based sauce', WP + 'Anticucho', W),
    'WP_BABA': ('Wikipedia, Baba ghanoush: roasted eggplant mixed with olive oil, lemon juice, seasonings and tahini (sesame paste)', WP + 'Baba_ghanoush', W),
    'WP_KIBB': ('Wikipedia, Kibbeh: shell made by "pounding bulgur wheat together with meat"; Levantine filling includes "toasted pine nuts and spices"; meatless Lebanese versions use onions, walnuts and wheat', WP + 'Kibbeh', W),
    'WP_ZAATAR': ('Wikipedia, Za\'atar: ground dried herbs (usually Origanum syriacum), salt and sumac; the traditional recipe calls for "roasted sesame seeds"', WP + 'Za%27atar', W),
    'WP_MAAM': ('Wikipedia, Ma\'amoul: dough of semolina and butter; fillings include dates, figs, walnuts and pistachios', WP + 'Ma%27amoul', W),
    'WP_KNAF': ('Wikipedia, Knafeh: spun pastry dough (kadayif) or semolina, soft cheese such as Nabulsi, sugar syrup, heated in butter, margarine or ghee; often garnished with crushed pistachios', WP + 'Knafeh', W),
    'WP_TABB': ('Wikipedia, Tabbouleh: parsley, bulgur, tomato, mint, onion; bulgur is a wheat product', WP + 'Tabbouleh', W),
    'WP_HMEE': ('Wikipedia, Hokkien mee: egg noodles and rice noodles stir-fried with egg, pork, prawns and squid; broth made with prawn heads and shells and pork bones', WP + 'Hokkien_mee', W),
    'WP_BKT': ('Wikipedia, Bak kut teh: pork ribs in a herbal broth with light and dark soy sauce; in Malaysia often served with strips of fried dough (you char kway)', WP + 'Bak_kut_teh', W),
    'WP_OYOM': ('Wikipedia, Oyster omelette: "starchy egg batter" thickened with sweet potato starch around small oysters, often fried in pork lard; may be topped with a sauce; shrimp can replace oysters', WP + 'Oyster_omelette', W),
    'WP_CCF': ('Wikipedia, Chee cheong fun: rice noodle rolls finished with sweetened soy sauce; Penang style served with shrimp paste (hae ko); Ipoh style adds sweet red sauce, chili and sesame seeds; fillings shrimp, beef or pork', WP + 'Chee_cheong_fun', W),
    'WP_BNG': ('Wikipedia, Biscuits and gravy: soft dough biscuits with white gravy made from "the drippings of cooked pork sausage, flour, milk"', WP + 'Biscuits_and_gravy', W),
}

# ------------------------------------------------------------------ rule tables
NB = r'(?<![a-z])'
BAKED = (r'\b(breads?|buns?|bagels?|baguettes?|toasts?|pitas?|naan|kulcha|roti|brioche|biscuits?|muffins?|croissants?|flatbreads?|'
         r'(?<!fish )(?<!rice )(?<!turnip )(?<!crab )cakes?|pies?|pastr(?:y|ies)|tarts?|cookies?|donuts?|doughnuts?|brownies?|waffles?|sandwich(?:es)?|burgers?|breadsticks?|'
         r'(?<!spring )(?<!summer )(?<!egg )(?<!rice )(?<!noodle )(?<!sushi )rolls?)\b')
SHELL = r'\b(shrimps?|prawns?|crabs?|lobsters?|crawfish|crayfish|krill|squid|calamari|octopus|clams?|mussels?|cockles?|oysters?(?! sauce)|scallops?|snails?|abalone|cuttlefish)\b'

# (allergen, regex, reason template, source)  {w} = the matched word
RULES_A = [
    ('MIL', r'(?<!coconut )(?<!soy )(?<!almond )(?<!oat )\bmilk\b|\b(cheese|buttermilk|(?<!coconut )cream|creamy|yogurt|yoghurt|ghee|custard|pudding|paneer|whey|lassi|ricotta|mozzarella|parmesan|feta|gorgonzola|labneh|halloumi|flan|condensed|evaporated|kheer|rasmalai|queso|leche)\b|(?<!peanut )(?<!nut )(?<!cocoa )(?<!almond )\bbutter\b', 'the menu names {w}, a milk food', 'PRINTED'),
    ('EGG', r'\b(eggs?|omelet(?:te)?s?|custard|flan|quiche|carbonara|frittata)\b', 'the menu names {w}', 'PRINTED'),
    ('PEA', r'\b(peanuts?|groundnuts?|satay|kacang)\b', 'the menu names {w}', 'PRINTED'),
    ('TRE', r'\b(almonds?|walnuts?|pecans?|pistachios?|cashews?|hazelnuts?|pine nuts?|macadamias?)\b', 'the menu names {w}', 'PRINTED'),
    ('SES', r'\b(sesame|tahini|halva)\b', 'the menu names {w}', 'PRINTED'),
    ('SOY', r'\b(soy|soya|soybeans?|tofu|miso|tempeh|edamame|tamari|shoyu|natto)\b', 'the menu names {w}', 'PRINTED'),
    ('FIS', r'\b(fish|anchov(?:y|ies)|salmon|tuna|cod|bream|catfish|lox|sardines?|mackerel|trout|snapper|tilapia|branzino|fishballs?)\b', 'the menu names {w}', 'PRINTED'),
    ('SHE', r'\b(shrimps?|prawns?|crabs?|lobsters?|crawfish|crayfish|krill)\b', 'the menu names {w}', 'PRINTED'),
    ('WHE', BAKED[:-3] + r'|pasta|spaghetti|pizza|dumplings?|flour|wheat|bulgur|couscous|semolina|batter|breaded|bread ?crumbs?|dough|instant noodles?|egg noodles?)\b', '{w} is wheat or made of wheat', 'BASIC'),
]
RULES_Q = [
    # sesame, FARE_SES3
    ('SES', BAKED, 'FARE lists baked goods, bread, buns and rolls as sesame sources ({w})', 'FARE_SES3'),
    ('SES', r'\b(sauces?|dressings?|gravy|gravies|marinad(?:e|es)|marinat(?:e|es|ed)|dips?|dipping)\b', 'FARE lists dressings, gravies, marinades and sauces as sesame sources ({w})', 'FARE_SES3'),
    ('SES', r'\b(soups?|stews?|stir-?fr(?:y|ied)|kebabs?|skewers?|sausages?|falafel|hummus|crackers?|tortilla chips|pita chips|granola|muesli|bread ?crumbs?|breaded|sushi|tempeh|margarine|pretzels?|rice cakes?|noodles?|fried rice|risotto|herbs?|herbal|candy)\b', 'FARE lists {w} (or flavored rice, noodles, soups, stews, stir fry, kebabs, sausages) as a sesame source', 'FARE_SES3'),
    # soy, FARE_SOY3
    ('SOY', BAKED, 'FARE lists baked goods and breads as soy sources ({w})', 'FARE_SOY3'),
    ('SOY', r'\b(sauces?|broth|soups?|stock|sausages?|hot dogs?|bacon|ham|salami|luncheon meat|corned beef|pastrami|ice cream|yogurt|pasta|tortillas?|crackers?|cereal|granola)\b', 'FARE lists {w} (sauces, soups and broths, processed meats, dairy desserts, pasta, tortillas) as a soy source', 'FARE_SOY3'),
    # wheat, FARE_WHE3
    ('WHE', r'\b(sauces?|dressings?|soups?|sausages?|hot dogs?|batter|battered|breaded|beer|surimi|imitation crab|marinara|ice cream|candy|cereal|crackers?|rice cakes?|crispy fried|fried chicken|deep-fried|tempura|fritters?)\b|soy sauce', 'FARE lists {w} (sauces, dressings, soups, sausages, batter-fried and breaded foods, soy sauce) as a wheat source', 'FARE_WHE3'),
    # egg, FARE_EGG3
    ('EGG', BAKED, 'FARE lists baked goods and breads (egg wash) as egg sources ({w})', 'FARE_EGG3'),
    ('EGG', r'\b(mayonnaise|mayo|hollandaise|meringue|merengue|souffl[eé]|dressings?|pasta|spaghetti|lasagna|ravioli|gnocchi|macaroni|pancakes?|french toast|buttercream|frosting|mousse|ice cream|sorbet|gelato|marzipan|marshmallows?|nougat|eggnog|pretzels?|tortillas?|latte|cappuccino|mocha|surimi|imitation crab)\b', 'FARE lists {w} as an egg source', 'FARE_EGG3'),
    # milk, FARE_MIL3
    ('MIL', BAKED, 'FARE lists baked goods and breads as milk sources ({w})', 'FARE_MIL3'),
    ('MIL', r'\b(pancakes?|cereal|granola|chocolate|sausages?|hot dogs?|luncheon meat|bologna|salami|margarine|pasta|tortillas?|pretzels?|crackers?|tuna|smoothie|latte|cappuccino|mocha|steak|caramel|nougat|sherbet|corned beef)\b', 'FARE lists {w} as a possible milk source', 'FARE_MIL3'),
    ('MIL', SHELL, 'FARE says shellfish is sometimes dipped in milk ({w})', 'FARE_MIL3'),
    # peanut, FARE_PEA3
    ('PEA', BAKED, 'FARE lists baked goods and pies as peanut sources ({w})', 'FARE_PEA3'),
    ('PEA', r'\b(chili sauce|hot sauce|pesto|gravy|mole|dressings?|glazes?|glazed|marinad(?:e|es)|marinat(?:e|es|ed)|enchilada sauce|egg rolls?|granola|pancakes?|pizza|ice cream|pudding|candy|chocolate|marzipan|nougat|trail mix|sunflower seeds?|hot chocolate|meat substitute|vegetarian burgers?)\b', 'FARE lists {w} as a possible peanut source', 'FARE_PEA3'),
    # tree nut, FARE_TRE3
    ('TRE', r'\b(pesto|marzipan|praline|gianduja|nut butters?|cereal|crackers?|cookies?|candy|chocolate|confection|energy bars?|marinad(?:e|es)|marinat(?:e|es|ed)|barbecue sauce|bbq|mortadella|granola|ice cream|gelato|sorbet|flavored coffee)\b', 'FARE lists {w} as a possible tree nut source', 'FARE_TRE3'),
    # fish, FARE_FIS3
    ('FIS', r'\b(barbecue|bbq|worcestershire|caesar|caponata|bouillabaisse|kimchi|surimi|imitation crab|fish stock|fish flavoring)\b', 'FARE lists {w} as a possible fish source', 'FARE_FIS3'),
    # shellfish, FARE_SHE3 and mollusc plans
    ('SHE', r'\b(bouillabaisse|fish stock|seafood flavoring|surimi|imitation crab|cuttlefish ink|squid ink)\b', 'FARE lists {w} as a possible shellfish source', 'FARE_SHE3'),
    ('SHE', r'\b(squid|calamari|octopus|clams?|mussels?|cockles?|oysters?|oyster sauce|scallops?|snails?|abalone|cuttlefish)\b', 'a mollusc ({w}) is not on the FDA crustacean list; many shellfish plans include it', 'GEN'),
]
# dish-name-only rule (the FARE item "Chili" means the stew)
NAME_RULES_Q = [('PEA', r'^chili\b|\bchili$', 'FARE lists chili (the stew) as a possible peanut source', 'FARE_PEA3')]

MENUS3 = []


def D3(name, price, desc='', *facts, sub='', en='', kw=''):
    fl = []
    for f in facts:
        if isinstance(f, En):
            en = str(f)
        else:
            fl.append(f)
    return {'name': name, 'price': price, 'desc': desc, 'facts': fl, 'sub': sub, 'en': en, 'kw': kw}


def menu(**kw):
    MENUS3.append(kw)


def dish_text(d):
    return ' '.join(x for x in (d['name'], d['sub'], d['desc'], d['en'], d['kw']) if x).lower()


def special(d):
    return len({f[0] for f in d['facts']}) == len(M.ALLERGENS)


def apply_rules():
    for m in MENUS3:
        for _, ds in m['sections']:
            for d in ds:
                if special(d):
                    continue
                t = dish_text(d)
                have = lambda c: any(f[0] == c for f in d['facts'])
                haveA = lambda c: any(f[0] == c and f[1] == 'A' for f in d['facts'])
                for c, rx, why, src in RULES_A:
                    mm = re.search(rx, t)
                    if mm and not haveA(c):
                        s = src
                        if c == 'PEA' and 'satay' in t:
                            s = 'AAA_PEA' if mm.group(0) == 'satay' else src
                        w = mm.group(0)
                        d['facts'].append(A(c, why.format(w=w), s))
                for c, rx, why, src in RULES_Q:
                    mm = re.search(rx, t)
                    if mm and not have(c):
                        d['facts'].append(Q(c, why.format(w=mm.group(0)), src))
                for c, rx, why, src in NAME_RULES_Q:
                    if re.search(rx, d['name'].lower()) and not have(c):
                        d['facts'].append(Q(c, why, src))


def check_rules():
    """Fail if any dish text matches a rule and the dish has no fact for that allergen (A rules need an A fact)."""
    n = 0
    for m in MENUS3:
        if m['lang'] != 'en':
            for _, ds in m['sections']:
                for d in ds:
                    assert d['en'] and (d['kw'] or special(d)), ('non-English dish needs en gloss and kw', m['id'], d['name'])
        for _, ds in m['sections']:
            for d in ds:
                t = dish_text(d)
                for c, rx, _, _ in RULES_A:
                    if re.search(rx, t):
                        assert any(f[0] == c and f[1] == 'A' for f in d['facts']), ('A rule not applied', m['id'], d['name'], c)
                        n += 1
                for c, rx, _, _ in RULES_Q:
                    if re.search(rx, t):
                        assert any(f[0] == c for f in d['facts']), ('Q rule not applied', m['id'], d['name'], c)
                        n += 1
    return n


S = lambda: ALLQ()

# ---------------------------------------------------------------- M33 Hong Kong cha chaan teng (zh, Traditional Chinese, photo)
menu(id='M33', title='金鳳茶餐廳', lang='zh', font='hiragino', bg='cream', style='photo', heldout=True, sections=[
    ('餐點與麵飯', [
        D3('餐肉蛋治', 'HK$30', '餐肉、煎蛋、方包', en='Luncheon meat and egg sandwich', kw='luncheon meat, fried egg, sandwich bread'),
        D3('乾炒牛河', 'HK$68', '河粉、牛肉、芽菜、豉油', en='Dry-fried beef chow fun', kw='rice noodles, beef, bean sprouts, soy sauce'),
        D3('星洲炒米', 'HK$62', '米粉、蝦、雞蛋、咖哩粉', en='Singapore-style fried vermicelli', kw='rice vermicelli noodles, shrimp, egg, curry powder'),
        D3('焗豬扒飯', 'HK$64', '豬扒、茄汁、芝士、白飯', en='Baked pork chop rice', kw='pork chop, tomato sauce, cheese, rice'),
        D3('咖哩魚蛋', 'HK$28', '魚肉丸、咖哩汁', en='Curry fish balls', kw='fish balls, curry sauce'),
        D3('沙嗲牛肉麵', 'HK$58', '沙嗲汁、牛肉、公仔麵', A('WHE', 'instant noodles are wheat', 'BASIC'), en='Satay beef noodles', kw='satay sauce, beef, instant noodles'),
        D3('今日例湯', 'HK$18', '請問店員', *S(), en='Daily set soup'),
    ]),
    ('點心與飲品', [
        D3('菠蘿油', 'HK$22', '菠蘿包夾厚切牛油', Q('EGG', 'the pineapple bun topping is made with eggs', 'WP_PBUN'), en='Pineapple bun with butter', kw='pineapple bun with a thick slice of butter'),
        D3('西多士', 'HK$32', '麵包、花生醬、雞蛋、煉奶', en='Hong Kong French toast', kw='bread, peanut butter, egg, condensed milk'),
        D3('港式奶茶', 'HK$20', '紅茶、淡奶', en='Hong Kong milk tea', kw='black tea, evaporated milk'),
        D3('鴛鴦', 'HK$22', '咖啡、奶茶', en='Coffee with milk tea', kw='coffee, milk tea'),
        D3('凍檸茶', 'HK$22', '紅茶、檸檬、糖', en='Iced lemon tea', kw='black tea, lemon, sugar'),
    ]),
])

# ---------------------------------------------------------------- M34 Vietnamese (vi, scan)
menu(id='M34', title='Bếp Nhà Hạnh', lang='vi', font='georgia', bg='white', style='scan', heldout=True, sections=[
    ('Món chính', [
        D3('Bánh Xèo', '45k', 'bánh giòn nghệ, tôm, thịt ba chỉ, giá, nước chấm',
           Q('FIS', 'nuoc cham is made from fish sauce; the menu does not say what is in the dipping sauce', 'WP_NUOC'), en='Crispy turmeric crepe',
           kw='crispy turmeric rice-flour crepe, shrimp, pork belly, bean sprouts, nuoc cham dipping sauce'),
        D3('Bún Thịt Nướng', '55k', 'thịt heo nướng, bún, rau thơm, đậu phộng, nước mắm pha',
           Q('FIS', 'nuoc mam pha is a fish sauce dressing', 'WP_NUOC'), en='Grilled pork vermicelli bowl',
           kw='grilled pork, rice vermicelli noodles, herbs, crushed peanuts, fish-sauce style dressing nuoc mam'),
        D3('Cá Kho Tộ', '110k', 'cá lóc kho trong nồi đất, nước màu, tiêu', en='Clay pot braised catfish', kw='catfish braised in a clay pot, caramel sauce, pepper'),
        D3('Canh Chua Tôm', '70k', 'canh chua tôm, dứa, cà chua, đậu bắp', en='Sour soup with shrimp', kw='sour soup with shrimp, pineapple, tomato, okra'),
        D3('Bò Lúc Lắc', '120k', 'bò thăn xào, nước tương, hành tây, cải xoong', en='Shaking beef', kw='stir-fried beef tenderloin, soy sauce, onion, watercress'),
        D3('Bánh Cuốn Nóng', '55k', 'bánh gạo hấp, thịt heo xay, mộc nhĩ, hành phi', en='Steamed rice rolls', kw='steamed rice rolls, ground pork, wood ear mushroom, fried shallots'),
        D3('Món Đặc Biệt Hôm Nay', '60k', 'hỏi nhân viên', *S(), en='Special of the day'),
    ]),
    ('Món cuốn và tráng miệng', [
        D3('Nem Nướng Cuốn', '65k', 'nem nướng, rau thơm, bánh tráng, tương đậu phộng', en='Grilled pork sausage rice-paper rolls', kw='grilled pork sausage, herbs, rice paper, peanut sauce'),
        D3('Cà Phê Trứng', '40k', 'cà phê, lòng đỏ trứng, sữa đặc', en='Egg coffee', kw='coffee, egg yolk, condensed milk'),
        D3('Bánh Flan', '30k', 'bánh flan caramel, cà phê', en='Caramel flan', kw='caramel flan, coffee'),
        D3('Chè Ba Màu', '35k', 'đậu xanh, đậu đỏ, thạch lá dứa, nước cốt dừa', en='Three-color dessert', kw='mung beans, red beans, pandan jelly, coconut milk'),
        D3('Nước Mía', '20k', 'nước mía tươi, quất', en='Sugarcane juice', kw='fresh sugarcane juice, kumquat'),
    ]),
])

# ---------------------------------------------------------------- M35 Thai street food (en, glare)
menu(id='M35', title='Soi 9 Night Market Kitchen', lang='en', font='verdana', bg='kraft', style='glare', heldout=True, sections=[
    ('From the grill and wok', [
        D3('Moo Ping', 'THB 50', 'grilled pork skewers marinated in garlic, coriander root and soy sauce, sticky rice'),
        D3('Khao Man Gai', 'THB 60', 'poached chicken rice, ginger and fermented soybean sauce, clear broth'),
        D3('Pad Kra Pao Kai Dao', 'THB 70', 'holy basil stir-fry with minced pork, oyster sauce and a fried egg on rice'),
        D3('Hoi Tod', 'THB 80', 'crispy mussel pancake, egg, bean sprouts, chili sauce'),
        D3('Gai Yang', 'THB 85', 'charcoal grilled half chicken, garlic and coriander marinade, sweet chili dip',
           Q('FIS', 'the traditional gai yang marinade is built on fish sauce', 'WP_GYANG'), Q('SOY', 'marinade variations add soy sauce or hoisin', 'WP_GYANG')),
        D3('Sai Oua', 'THB 70', 'Northern herb sausage, lemongrass, galangal, kaffir lime',
           Q('FIS', 'sai oua is seasoned with fish sauce', 'WP_SAIUA')),
    ]),
    ('Noodles, salads and sweets', [
        D3('Khao Soi', 'THB 90', 'northern curry noodle soup, egg noodles, coconut curry, crispy noodles, pickled mustard greens'),
        D3('Larb Moo', 'THB 75', 'minced pork salad, toasted rice powder, mint, lime, fish sauce'),
        D3('Roti Gluay', 'THB 40', 'griddled flatbread, banana, egg, sweetened condensed milk'),
        D3('Mango Sticky Rice', 'THB 90', 'ripe mango, sticky rice, coconut cream, mung beans'),
        D3("Vendor's Choice of the Day", 'THB 60', 'ask at the stall', *S()),
        D3('Fresh Coconut Water', 'THB 30', 'young coconut'),
    ]),
])

# ---------------------------------------------------------------- M36 Indian (en, clean)
menu(id='M36', title='Saffron Lane Indian Kitchen', lang='en', font='optima', bg='white', style='clean', heldout=True, sections=[
    ('Curries and grill', [
        D3('Chicken Tikka Masala', '$18', 'tandoori chicken in spiced tomato and cream sauce'),
        D3('Lamb Rogan Josh', '$20', 'braised lamb, Kashmiri chili, fennel, ginger', Q('MIL', 'rogan josh is often made with yogurt, which the menu does not print')),
        D3('Dal Makhani', '$15', 'black lentils cooked overnight, kidney beans, tomato',
           A('MIL', 'dal makhani is made with butter and cream', 'WP_DMAKH')),
        D3('Paneer Tikka', '$16', 'cottage cheese cubes marinated in yogurt and spices, grilled'),
        D3('Goan Prawn Curry', '$22', 'prawns in coconut and tamarind curry'),
        D3('Aloo Gobi', '$13', 'potato and cauliflower, turmeric, cumin'),
    ]),
    ('Breads, small plates and sweets', [
        D3('Poha', '$10', 'flattened rice with peanuts, mustard seed, curry leaf, lemon'),
        D3('Amritsari Kulcha', '$7', 'stuffed leavened flatbread baked in the tandoor'),
        D3('Chicken 65', '$14', 'fried chicken bites, yogurt, curry leaves, chili',
           Q('WHE', 'chicken 65 is usually coated in flour or corn flour before frying')),
        D3('Gajar Halwa', '$8', 'grated carrot cooked in milk and ghee, almonds, cashews'),
        D3("Chef's Tandoor Special", '$24', 'the catch of the day from the clay oven, ask your server', *S()),
        D3('Cucumber Raita', '$5', 'whisked yogurt, cucumber, roasted cumin'),
    ]),
])

# ---------------------------------------------------------------- M37 Peruvian (es, blur)
menu(id='M37', title='La Huaca Cocina Peruana', lang='es', font='palatino', bg='cream', style='blur', heldout=True, sections=[
    ('Entradas y platos', [
        D3('Tiradito Nikkei', 'S/ 42', 'pescado blanco en láminas, crema de ají amarillo, sillao, limón', en='Sliced raw white fish in yellow chili cream',
           kw='raw white fish slices, yellow chili cream sauce, soy sauce, lime'),
        D3('Lomo Saltado', 'S/ 48', 'lomo de res salteado, cebolla, tomate, papas fritas, arroz', A('SOY', 'soy sauce is a main ingredient of lomo saltado', 'WP_LOMO'),
           en='Stir-fried beef loin', kw='stir-fried beef loin, onion, tomato, french fries, rice'),
        D3('Ají de Gallina', 'S/ 38', 'pollo deshilachado en crema de ají amarillo, huevo, aceitunas, arroz',
           A('WHE', 'ají de gallina is thickened with bread', 'WP_AJI'), Q('TRE', 'the sauce is often thickened with ground walnuts or pecans, which the menu does not print', 'WP_AJI'),
           en='Shredded chicken in yellow chili cream', kw='shredded chicken in yellow chili cream sauce, egg, olives, rice'),
        D3('Papa a la Huancaína', 'S/ 28', 'papa amarilla, salsa de queso fresco, huevo duro, aceituna', en='Potato in fresh cheese sauce',
           kw='yellow potato, fresh cheese sauce, hard-boiled egg, olive'),
        D3('Anticuchos de Corazón', 'S/ 36', 'brochetas de corazón de res marinadas en ají panca, con papa y choclo', en='Beef heart skewers',
           kw='skewers of beef heart marinated in panca chili, with potato and corn'),
        D3('Arroz Chaufa de Mariscos', 'S/ 46', 'arroz frito con camarones, calamares, huevo, sillao', en='Seafood fried rice',
           kw='fried rice with shrimp, squid, egg, soy sauce'),
        D3('Causa Limeña', 'S/ 30', 'masa de papa amarilla, pollo, mayonesa, palta', en='Layered yellow potato terrine', kw='yellow potato dough, chicken, mayonnaise, avocado'),
    ]),
    ('Postres, antojos y bebidas', [
        D3('Choclo con Queso', 'S/ 18', 'maíz peruano, queso andino', en='Peruvian corn with cheese', kw='Peruvian corn, Andean cheese'),
        D3('Picarones', 'S/ 24', 'buñuelos de zapallo y camote, miel de chancaca', en='Squash and sweet potato doughnuts', kw='squash and sweet potato doughnuts, chancaca syrup'),
        D3('Suspiro a la Limeña', 'S/ 22', 'leche condensada, merengue de oporto', en='Milk caramel with port meringue', kw='condensed milk, port meringue'),
        D3('Sugerencia del Chef', 'S/ 45', 'consulte con su mesero', *S(), en="Chef's suggestion"),
        D3('Chicha Morada', 'S/ 12', 'maíz morado, piña, canela, limón', en='Purple corn drink', kw='purple corn, pineapple, cinnamon, lime'),
    ]),
])

# ---------------------------------------------------------------- M38 American brunch (en, photo)
menu(id='M38', title='Maple & Main Brunch House', lang='en', font='optima', bg='cream', style='photo', heldout=True, sections=[
    ('Plates', [
        D3('Chicken and Waffles', '$19', 'crispy fried chicken thigh, malted waffle, maple syrup'),
        D3('Biscuits and Sausage Gravy', '$14', 'split biscuits, pork sausage gravy', A('MIL', 'sausage gravy is made with milk', 'WP_BNG')),
        D3('Shrimp and Grits', '$22', 'sauteed shrimp, stone-ground grits, bacon, scallions'),
        D3('Lox and Bagel', '$17', 'smoked salmon, cream cheese, capers, red onion, toasted bagel'),
        D3('Breakfast Burrito', '$15', 'scrambled eggs, chorizo, potatoes, cheddar, flour tortilla'),
        D3('Banana Walnut French Toast', '$16', 'thick brioche, walnut crumble, banana, maple butter'),
        D3('Corned Beef Hash', '$16', 'house-cured corned beef, potatoes, onions, two eggs any style'),
    ]),
    ('Light bites and sides', [
        D3('Berry Parfait', '$11', 'Greek yogurt, granola, mixed berries, honey'),
        D3('Skillet of the Day', '$17', 'ask your server what the kitchen made today', *S()),
        D3('Seasonal Melon Plate', '$9', 'cantaloupe, honeydew, mint'),
        D3('Home Fries', '$6', 'roasted potatoes, onion, paprika'),
        D3('Cold-Pressed Grapefruit Juice', '$6', 'grapefruit'),
    ]),
])

# ---------------------------------------------------------------- M39 Lebanese (en, clean)
menu(id='M39', title='Beit Al Mezze', lang='en', font='cochin', bg='cream', style='clean', heldout=True, sections=[
    ('Mezze', [
        D3('Kibbeh Mekliyeh', '$14', 'fried bulgur and lamb shells filled with spiced meat and pine nuts', A('WHE', 'the shell is made of bulgur wheat', 'WP_KIBB')),
        D3('Muhammara', '$11', 'roasted red pepper, walnuts, pomegranate molasses, breadcrumbs'),
        D3("Manakish Za'atar", '$8', "baked flatbread topped with za'atar and olive oil", Q('SES', "za'atar blends traditionally include roasted sesame seeds, which the menu does not print", 'WP_ZAATAR')),
        D3('Fatteh', '$13', 'toasted pita, warm chickpeas, garlic yogurt, pine nuts'),
        D3('Mujaddara', '$12', 'lentils, rice, caramelized onions'),
        D3('Warak Enab', '$12', 'grape leaves stuffed with rice, tomato, parsley, olive oil'),
        D3("Chef's Mezze Selection", '$26', 'changes daily, ask your server', *S()),
    ]),
    ('Grill and sweets', [
        D3('Shish Taouk', '$19', 'garlic marinated chicken skewers, toum, pickles'),
        D3('Kafta Skewers', '$18', 'grilled minced lamb and parsley skewers'),
        D3("Ma'amoul", '$9', 'semolina cookies filled with dates', A('WHE', 'the dough is made of semolina', 'WP_MAAM'), A('MIL', 'the dough is made with butter', 'WP_MAAM'),
           Q('TRE', 'ma\'amoul fillings include walnuts and pistachios, which the menu does not print', 'WP_MAAM')),
        D3('Knafeh', '$11', 'shredded pastry, sweet white cheese, orange blossom syrup', Q('TRE', 'knafeh is often garnished with crushed pistachios', 'WP_KNAF')),
        D3('Lemon Mint Lemonade', '$6', 'lemon, mint, sugar'),
    ]),
])

# ---------------------------------------------------------------- M40 Chinese-Malaysian kopitiam (en, glare)
menu(id='M40', title='Kedai Kopi Ah Hock', lang='en', font='rockwell', bg='kraft', style='glare', heldout=True, sections=[
    ('Noodles and rice', [
        D3('Hokkien Mee', '$12', 'egg noodles and rice noodles wok-fried with prawns, squid, pork and prawn stock'),
        D3('Bak Kut Teh', '$14', 'pork rib herbal soup with dark soy sauce and garlic, fried dough fritters'),
        D3('Oyster Omelette', '$13', 'eggs, small oysters, starch batter, chili dip'),
        D3('Chee Cheong Fun', '$9', 'steamed rice noodle rolls with sweet sauce and shrimp paste', Q('SES', 'Ipoh-style chee cheong fun is topped with sesame seeds', 'WP_CCF')),
        D3('Hainanese Chicken Rice', '$11', 'poached chicken, fragrant rice, ginger paste, dark soy sauce'),
        D3('Curry Mee', '$11', 'noodles in coconut curry broth with tofu puffs, cockles and chili paste'),
    ]),
    ('Kopitiam favorites', [
        D3('Ipoh Bean Sprout Chicken', '$15', 'poached chicken, blanched bean sprouts, light soy dressing'),
        D3('Kaya Toast Set', '$7', 'toasted bread, kaya coconut jam, butter, two soft-boiled eggs'),
        D3('Pandan Chiffon Slice', '$5', 'pandan sponge cake'),
        D3('Ais Kacang', '$6', 'shaved ice, red beans, sweet corn, grass jelly, evaporated milk, palm sugar',
           Q('PEA', 'ais kacang is often topped with crushed peanuts, which the menu does not print')),
        D3('Kopi O', '$3', 'black coffee, sugar'),
        D3('Kopitiam Special of the Day', '$10', 'ask the staff at the counter', *S()),
    ]),
])

apply_rules()
_used = {f[3] for m in MENUS3 for _, ds in m['sections'] for d in ds for f in d['facts']}
M.SOURCES.update({k: v for k, v in SOURCES3.items() if k in _used})
