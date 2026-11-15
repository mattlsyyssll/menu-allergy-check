"""Menu content and allergen facts for HELD-OUT SET 4 (M41-M48). Pure data plus one rule engine; uses the helpers of the frozen tools/menus_data.py.

Key policy of sets 1 and 2 (NOT the per-dish category lines of set 3):
- Per dish and allergy list, the strictest fact wins.
- Avoid (A): the menu prints the allergen, or it is a basic ingredient of the named dish.
- Ask the kitchen (Q): (a) a public source names THIS dish, or a NAMED FOOD that is part of it (sauce, dip, paste, bread, batter, dressing by name),
  as a possible source; every such named-food rule is applied by code to EVERY dish whose text contains that food (RULES_Q below);
  or (b) the menu does not say what is in the dish ("of the day", "special", "chef's choice").
- NOT counted: category, cuisine or cross-contact lines that name no specific food ("baked goods", "sauces, dressings, gravies and marinades",
  "soups", "stews", "stir fry", "Asian cuisine", "shellfish sometimes dipped in milk", shared fryer oil). A named item inside such a line counts.
- Otherwise: No listed allergen found.
check_rules() fails the build if any dish text contains a named food (or an Avoid word) and has no fact for that allergen.
Matching runs over printed name, subtitle, description, English gloss and `kw` (plain English translation of the printed line, for non-English menus).
Written before any run; keys hashed in KEYS-HASHES.txt.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
import menus_data as M  # noqa: E402
from menus_data import A, Q, En, ALLQ  # noqa: E402

W = 'fetched 2026-11-14 (page-fetch summary)'
W4 = 'fetched 2026-11-14 (page-fetch summary, set 4)'
WP = 'https://en.wikipedia.org/wiki/'
FARE = 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/'
SOURCES4 = {
    'FARE_SES3': ('FARE sesame page, full "Foods That May Contain Sesame" list: Asian cuisine; baked goods (bagels, bread, breadsticks, hamburger buns and rolls); bread crumbs; cereals (granola, muesli); chips (bagel, pita, tortilla); crackers; dipping sauces (baba ghanoush, hummus, tahini sauce); dressings, gravies, marinades and sauces; falafel; hummus; flavored rice, noodles, risotto, shish kebabs, stews and stir fry; goma-dofu; herbs and herbal drinks; margarine; pasteli; processed meats and sausages; protein bars; snack foods (pretzels, candy, halvah, rice cakes); soups; sushi; tempeh; Turkish cake; vegetarian burgers', FARE + 'sesame', W),
    'FARE_SOY3': ('FARE soy page, named and unexpected sources: soy sauce, miso, tofu, tempeh, edamame, tamari, shoyu, natto, soy flour; grains prepared with soy (cereals, breads, chips, crackers, pasta, rice, tortillas); vegetable broth; baked goods, canned broths and soups, canned tuna and meat, cereals, cookies, crackers, dairy products (ice cream, yogurt), processed meats, sauces, sausages; Asian cuisine (Chinese, Indian, Indonesian, Thai, Vietnamese)', FARE + 'soy', W),
    'FARE_WHE3': ('FARE wheat page, hidden sources: soy sauce, surimi, imitation crab meat, batter-fried foods, breaded foods, baked goods, beer and ale, candy, crackers, hot dogs, ice cream, marinara sauce, processed meats, salad dressings, sauces, sausages, soups, breakfast cereals; bread crumbs, couscous, bulgur, semolina, flour, pasta are wheat', FARE + 'wheat', W),
    'FARE_EGG3': ('FARE egg page, named and hidden sources: mayonnaise, meringue, hollandaise, souffle, salad dressings, marzipan, marshmallows, nougat, eggnog, surimi; most commercial cooked pasta; baked goods; breads (may be coated with an egg wash); breakfast foods (pancakes, waffles); cake fillings (buttercream, frosting, mousse); ice cream, custard, sorbet; pretzels; tortillas; specialty coffee drinks (egg foam)', FARE + 'egg', W),
    'FARE_MIL3': ('FARE milk page: butter, buttermilk, cheese, cream, custard, ghee, pudding, sour cream, whey, yogurt; hidden sources: baked goods and desserts, breakfast foods (cereals, pancakes, waffles), caramel candies, chocolate, luncheon meat, hot dogs and sausages, margarine, nougat, pantry staples (breads, pasta, tortillas), shellfish (sometimes dipped in milk), sherbet, snack foods (chips, crackers, pretzels), tuna fish, specialty beverages (smoothies, lattes), butter on grilled steaks', FARE + 'milk', W),
    'FARE_FIS3': ('FARE fish page: fish flavoring, fish gelatin, fish oil, fish sticks; unexpected sources: barbecue sauce, bouillabaisse, Caesar salad and dressing, caponata, surimi (imitation fish or shellfish), Worcestershire sauce, kimchi made with fish sauce; African, Chinese, Indonesian, Thai and Vietnamese cuisines', FARE + 'fish', W),
    'FARE_PEA3': ('FARE peanut page, hidden sources: African, Asian and Mexican restaurant food; baked goods, pies, cookies, pudding, hot chocolate, candy, chocolate, ice creams, pancakes, granola, trail mix, marzipan, nougat, chili, egg rolls, enchilada sauce, glazes and marinades, sauces (chili sauce, hot sauce, pesto, gravy, mole sauce, salad dressing), specialty pizzas, vegetarian meat substitutes', FARE + 'peanut', W),
    'FARE_TRE3': ('FARE tree nut page, hidden sources: pesto, marzipan/almond paste, gianduja, praline, nut milks, nut butters, nut oils, cereals, crackers, cookies, candy, chocolates, confections, energy bars, flavored coffee, frozen desserts, marinades, barbecue sauces, some cold cuts such as mortadella; coconut is not usually restricted', FARE + 'tree-nut', W),
    'FARE_SHE3': ('FARE shellfish page: bouillabaisse, cuttlefish ink, glucosamine, fish stock, seafood flavoring (crab or clam extract), fish stock or fish sauce sometimes made from krill, surimi', FARE + 'shellfish', W),
    'WP_KNAF': ('Wikipedia, Knafeh: spun pastry dough (kadayif) or semolina, soft cheese such as Nabulsi, sugar syrup, heated in butter, margarine or ghee; often garnished with crushed pistachios', WP + 'Knafeh', W),
    'WP_DASHI': ('Wikipedia, Dashi: katsuobushi is preserved, fermented skipjack tuna and niboshi are small dried sardines; kombu and shiitake dashi are fish-free', WP + 'Dashi', W),
    'WP_YAKI': ('Wikipedia, Yakitori: tare glaze consists of "mirin, sake, soy sauce, and sugar"', WP + 'Yakitori', W),
    'WP_DOUBAN': ('Wikipedia, Doubanjiang: "made from fermented broad beans (fava beans), chili peppers, soybeans, salt, and flour"', WP + 'Doubanjiang', W4),
    'WP_TARTAR': ('Wikipedia, Tartar sauce: "based on either mayonnaise or aioli", with pickles and lemon juice', WP + 'Tartar_sauce', W4),
    'WP_NITER': ('Wikipedia, Niter kibbeh: "a seasoned, clarified butter" simmered with spices; a vegetable-oil version replaces the butter', WP + 'Niter_kibbeh', W4),
    'WP_DORO': ('Wikipedia, Doro wat: often includes a peeled hard-boiled egg; niter kibbeh (seasoned clarified butter) is usually the fat', WP + 'Doro_wat', W4),
    'WP_SCHNITZ': ('Wikipedia, Wiener Schnitzel: the cutlet is "rolled in flour, whipped eggs, and bread crumbs"', WP + 'Wiener_Schnitzel', W4),
    'WP_SPAETZ': ('Wikipedia, Spaetzle: dough "typically consists of few ingredients, principally eggs, flour, and salt"; Kaesespaetzle adds grated cheese and fried onion', WP + 'Sp%C3%A4tzle', W4),
    'WP_PDQ': ('Wikipedia, Pao de queijo: made with cassava flour, eggs, milk and cheese (Minas, Canastra, Parmesan or mozzarella); optional butter or margarine', WP + 'P%C3%A3o_de_queijo', W4),
    'WP_KARE': ('Wikipedia, Kare-kare: stew "flavored with ground roasted peanuts or peanut butter, onions, and garlic"; often served with "bagoong alamang (sauteed salted shrimp paste)"', WP + 'Kare-kare', W4),
    'WP_ISKEN': ('Wikipedia, Iskender kebap: sliced grilled lamb over pieces of pita bread, hot tomato sauce, melted sheep\'s milk butter, yogurt served alongside', WP + '%C4%B0skender_kebap', W4),
    'WP_COXIN': ('Wikipedia, Coxinha: dough "made with wheat flour and chicken broth"; coated with batter, then breadcrumbs or manioc flour, then deep fried', WP + 'Coxinha', W4),
    'WP_SISIG': ('Wikipedia, Sisig: seasoned with calamansi, onions and chili peppers; chicken liver in some versions; egg and mayonnaise only in modern variations', WP + 'Sisig', W4),
}

NB = r'(?<![a-z])'
BREAD = (r'breads?|buns?|(?<!spring )(?<!egg )(?<!summer )(?<!sushi )(?<!rice paper )rolls?|bagels?|breadsticks?|bread ?crumbs?')
PASTA = r'pasta|spaghetti|ziti|rigatoni|penne|lasagna|ravioli|gnocchi|macaroni|fettuccine|linguine'
SHELL = r'squid|calamari|octopus|clams?|mussels?|cockles?|oysters?|oyster sauce|scallops?|snails?|abalone|cuttlefish'

# (allergen, regex, reason template, source). {w} = matched word
RULES_A = [
    ('MIL', r'(?<!coconut )(?<!soy )(?<!almond )(?<!oat )\bmilk\b|\b(cheese|buttermilk|(?<!coconut )cream|yogurt|yoghurt|ghee|custard|pudding|paneer|whey|ricotta|mozzarella|parmesan|feta|gorgonzola|labneh|halloumi|flan|condensed|evaporated|ice cream|gelato|milkshake|leche)\b|(?<!peanut )(?<!nut )(?<!cocoa )(?<!almond )\bbutter\b', 'the menu names {w}, a milk food', 'PRINTED'),
    ('EGG', r'\b(eggs?|omelet(?:te)?s?|custard|flan|quiche|carbonara|frittata)\b', 'the menu names {w}', 'PRINTED'),
    ('PEA', r'\b(peanuts?|groundnuts?|satay)\b', 'the menu names {w}', 'PRINTED'),
    ('TRE', r'\b(almonds?|walnuts?|pecans?|pistachios?|cashews?|hazelnuts?|pine nuts?|macadamias?)\b', 'the menu names {w}', 'PRINTED'),
    ('SES', r'\b(sesame|tahini|halva)\b', 'the menu names {w}', 'PRINTED'),
    ('SOY', r'\b(soy|soya|soybeans?|tofu|miso|tempeh|edamame|tamari|shoyu|natto)\b', 'the menu names {w}', 'PRINTED'),
    ('FIS', r'\b(fish|anchov(?:y|ies)|salmon|tuna|cod|bream|catfish|sardines?|mackerel|trout|snapper|bonito|katsuobushi)\b', 'the menu names {w}', 'PRINTED'),
    ('SHE', r'\b(shrimps?|prawns?|crabs?|lobsters?|crawfish|crayfish|krill)\b', 'the menu names {w}', 'PRINTED'),
    ('WHE', r'\b(' + BREAD + r'|pretzels?|(?<!fish )(?<!rice )(?<!turnip )(?<!crab )cakes?|cheesecake|pastr(?:y|ies)|strudel|pies?|tarts?|cookies?|graham crackers?|' + PASTA + r'|pizza|dumplings?|wontons?|ramen|flour|wheat|bulgur|couscous|semolina|dough)\b', '{w} is wheat or made of wheat', 'BASIC'),
]
RULES_Q = [
    # sesame: FARE_SES3 named foods (bread, buns, rolls, bagels, breadsticks, bread crumbs, hummus, baba ghanoush, falafel, crackers, granola, muesli, chips, pretzels, sushi, tempeh, rice cakes, sausages, shish kebabs, margarine, vegetarian burgers)
    ('SES', r'\b(' + BREAD + r'|hummus|baba ghanoush|falafel|crackers?|granola|muesli|pita chips|tortilla chips|bagel chips|pretzels?|sushi|tempeh|rice cakes?|sausages?|shish kebabs?|margarine|vegetarian burgers?)\b', 'FARE names {w} as a possible sesame source', 'FARE_SES3'),
    # soy: FARE_SOY3 named foods in the plain list (the "grains prepared with soy" line is a qualifier line, not applied)
    ('SOY', r'\b(cookies?|crackers?|cereals?|ice cream|yogurt|yoghurt|sausages?|vegetable broth)\b', 'FARE names {w} as a possible soy source', 'FARE_SOY3'),
    ('SOY', r'\b(doubanjiang|chili bean paste)\b', 'doubanjiang is made with soybeans and flour', 'WP_DOUBAN'),
    ('SOY', r'\btare\b', 'the tare glaze is made with soy sauce', 'WP_YAKI'),
    # wheat: FARE_WHE3 named foods
    ('WHE', r'\b(soy sauce|surimi|imitation crab|batter|battered|breaded|beer|ale|candy|crackers?|hot dogs?|ice cream|marinara|sausages?|cereals?)\b', 'FARE names {w} as a possible wheat source', 'FARE_WHE3'),
    ('WHE', r'\b(doubanjiang|chili bean paste)\b', 'doubanjiang is made with soybeans and flour', 'WP_DOUBAN'),
    ('WHE', r'\btare\b', 'the tare glaze is made with soy sauce, which sometimes holds wheat', 'WP_YAKI'),
    # egg: FARE_EGG3 named foods
    ('EGG', r'\b(mayonnaise|mayo|hollandaise|meringue|souffl[eé]|marzipan|marshmallows?|nougat|eggnog|surimi|imitation crab|' + PASTA + r'|' + BREAD + r'|pancakes?|waffles?|buttercream|frosting|mousse|ice cream|sorbet|pretzels?|tortillas?)\b', 'FARE names {w} as a possible egg source', 'FARE_EGG3'),
    ('EGG', r'\btartar sauce\b', 'tartar sauce is built on mayonnaise', 'WP_TARTAR'),
    # milk: FARE_MIL3 named foods
    ('MIL', r'\b(' + BREAD + r'|' + PASTA + r'|tortillas?|pancakes?|waffles?|cereals?|chocolate|caramel|luncheon meat|hot dogs?|sausages?|margarine|nougat|tuna|smoothies?|lattes?|steaks?|sherbet|crackers?|pretzels?|potato chips|tortilla chips)\b', 'FARE names {w} as a possible milk source', 'FARE_MIL3'),
    ('MIL', r'\bniter kibbeh\b', 'niter kibbeh is a seasoned clarified butter', 'WP_NITER'),
    # peanut: FARE_PEA3 named foods
    ('PEA', r'\b(chili sauce|hot sauce|pesto|gravy|mole|enchilada sauce|egg rolls?|marzipan|nougat|granola|trail mix|pancakes?|pies?|cookies?|pudding|hot chocolate|chocolate|candy|ice cream)\b', 'FARE names {w} as a possible peanut source', 'FARE_PEA3'),
    # tree nut: FARE_TRE3 named foods
    ('TRE', r'\b(pesto|marzipan|almond paste|praline|gianduja|nut butters?|nut milks?|cereals?|crackers?|cookies?|candy|chocolates?|energy bars?|barbecue sauce|mortadella|granola|flavored coffee)\b', 'FARE names {w} as a possible tree nut source', 'FARE_TRE3'),
    # fish: FARE_FIS3 named foods
    ('FIS', r'\b(barbecue sauce|bouillabaisse|caesar|caponata|surimi|imitation crab|worcestershire|kimchi|fish stock|fish flavoring)\b', 'FARE names {w} as a possible fish source', 'FARE_FIS3'),
    ('FIS', r'\bdashi\b', 'dashi is usually made with katsuobushi (bonito) or dried sardines', 'WP_DASHI'),
    # shellfish: FARE_SHE3 named foods, plus mollusc plans
    ('SHE', r'\b(fish sauce|fish stock|bouillabaisse|seafood flavoring|surimi|imitation crab|cuttlefish ink|squid ink)\b', 'FARE names {w} as a possible shellfish source (krill)', 'FARE_SHE3'),
    ('SHE', r'\b(' + SHELL + r')\b', 'a mollusc ({w}) is not on the FDA crustacean list; many shellfish plans include it', 'GEN'),
]
NAME_RULES_Q = [('PEA', r'^chili\b|\bchili$', 'FARE names chili (the stew) as a possible peanut source', 'FARE_PEA3')]

MENUS4 = []


def D3(name, price, desc='', *facts, sub='', en='', kw=''):
    fl = []
    for f in facts:
        if isinstance(f, En):
            en = str(f)
        else:
            fl.append(f)
    return {'name': name, 'price': price, 'desc': desc, 'facts': fl, 'sub': sub, 'en': en, 'kw': kw}


def menu(**kw):
    MENUS4.append(kw)


def dish_text(d):
    return ' '.join(x for x in (d['name'], d['sub'], d['desc'], d['en'], d['kw']) if x).lower()


def special(d):
    return len({f[0] for f in d['facts']}) == len(M.ALLERGENS)


def apply_rules():
    for m in MENUS4:
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
                        d['facts'].append(A(c, why.format(w=mm.group(0)), 'AAA_PEA' if (c == 'PEA' and mm.group(0) == 'satay') else src))
                for c, rx, why, src in RULES_Q:
                    mm = re.search(rx, t)
                    if mm and not have(c):
                        d['facts'].append(Q(c, why.format(w=mm.group(0)), src))
                for c, rx, why, src in NAME_RULES_Q:
                    if re.search(rx, d['name'].lower()) and not have(c):
                        d['facts'].append(Q(c, why, src))


def check_rules():
    """Fail if any dish text holds an Avoid word or a named food and the dish lacks the fact for that allergen."""
    n = 0
    for m in MENUS4:
        for _, ds in m['sections']:
            for d in ds:
                if m['lang'] != 'en':
                    assert d['en'] and (d['kw'] or special(d)), ('non-English dish needs en gloss and kw', m['id'], d['name'])
                if special(d):
                    continue
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

# ---------------------------------------------------------------- M41 Japanese ramen and izakaya (ja, photo)
menu(id='M41', title='麺屋 いろは', lang='ja', font='unicode', bg='kraft', style='photo', heldout=True, sections=[
    ('らーめん', [
        D3('豚骨ラーメン', '¥980', '豚骨スープ、中華麺、チャーシュー、ねぎ', en='Tonkotsu pork bone ramen', kw='pork bone broth, ramen wheat noodles, braised pork slices, scallion'),
        D3('味噌バターラーメン', '¥1,050', '味噌スープ、中華麺、コーン、バター', en='Miso butter ramen', kw='miso broth, ramen wheat noodles, corn, butter'),
        D3('醤油らーめん', '¥950', '鶏ガラ醤油スープ、中華麺、メンマ、海苔', en='Soy sauce ramen', kw='chicken bone soy sauce broth, ramen wheat noodles, bamboo shoots, nori seaweed'),
        D3('冷やし中華', '¥900', '冷やし麺、錦糸卵、きゅうり、ハム、ごまだれ', en='Chilled ramen noodle salad', kw='chilled ramen wheat noodles, shredded egg omelet, cucumber, ham, sesame sauce'),
        D3('焼き餃子', '¥480', '豚肉と野菜の餃子、酢醤油', en='Pan-fried pork dumplings', kw='pan-fried dumplings with pork and vegetables, vinegar and soy sauce for dipping'),
        D3('店長のきまぐれ一品', '¥600', '店員にお尋ねください', *S(), en="Manager's own small plate"),
    ]),
    ('一品料理とお飲み物', [
        D3('揚げ出し豆腐', '¥520', '片栗粉で揚げた豆腐、だし汁、大根おろし', en='Fried tofu in broth', kw='tofu fried in potato starch, dashi broth, grated daikon radish'),
        D3('手羽先の甘辛だれ', '¥580', '揚げ手羽先、甘辛だれ、白ごま', en='Fried chicken wings in sweet-savory sauce', kw='fried chicken wings, sweet-savory tare sauce, white sesame'),
        D3('チキン南蛮', '¥780', '卵衣で揚げた鶏もも肉、甘酢、タルタルソース', en='Chicken nanban', kw='chicken thigh fried in egg batter, sweet vinegar sauce, tartar sauce'),
        D3('冷奴', '¥380', '冷たい豆腐、かつお節、おろし生姜、ねぎ', en='Chilled tofu', kw='chilled tofu, bonito flakes, grated ginger, scallion'),
        D3('冷やしトマト', '¥350', 'トマト、塩', en='Chilled tomato', kw='tomato, salt'),
        D3('烏龍茶', '¥300', '温かいお茶または冷たいお茶', en='Oolong tea', kw='hot or iced oolong tea'),
    ]),
])

# ---------------------------------------------------------------- M42 Sichuan (zh, Simplified Chinese, glare)
menu(id='M42', title='蜀味轩', lang='zh', font='hiragino', bg='cream', style='glare', heldout=True, sections=[
    ('热菜与凉菜', [
        D3('回锅肉', '¥48', '五花肉、青蒜、豆瓣酱', en='Twice-cooked pork', kw='pork belly, garlic sprouts, doubanjiang chili bean paste'),
        D3('水煮牛肉', '¥68', '牛肉片、豆芽、干辣椒、花椒油', en='Sichuan boiled beef', kw='beef slices, bean sprouts, dried chili, Sichuan pepper oil'),
        D3('口水鸡', '¥42', '白切鸡、红油、花椒、芝麻、花生碎', en='Mouth-watering chicken', kw='poached chicken, chili oil, Sichuan pepper, sesame, crushed peanuts'),
        D3('夫妻肺片', '¥46', '牛肉、牛杂、红油、花椒面', en='Sliced beef and offal in chili oil', kw='beef and beef offal slices, chili oil, Sichuan pepper powder'),
        D3('干煸四季豆', '¥38', '四季豆、肉末、芽菜、干辣椒', en='Dry-fried green beans', kw='green beans, minced pork, pickled mustard greens, dried chili'),
        D3('蒜泥白肉', '¥42', '五花肉片、蒜泥、酱油、红油', en='Sliced pork with garlic sauce', kw='sliced boiled pork belly, garlic, soy sauce, chili oil'),
        D3('今日特色菜', '¥58', '请询问服务员', *S(), en="Kitchen's own dish for today"),
    ]),
    ('小吃与甜品', [
        D3('酸辣粉', '¥28', '红薯粉、花生碎、醋、红油', en='Hot and sour glass noodles', kw='sweet potato starch noodles, crushed peanuts, vinegar, chili oil'),
        D3('红油抄手', '¥32', '猪肉馄饨、红油、蒜泥', en='Wontons in chili oil', kw='pork wontons, chili oil, garlic'),
        D3('钟水饺', '¥30', '猪肉水饺、甜酱油、红油、蒜', en='Zhong dumplings', kw='pork dumplings, sweet soy sauce, chili oil, garlic'),
        D3('红糖糍粑', '¥22', '糯米糍粑、红糖、黄豆粉', en='Brown sugar glutinous rice cake', kw='glutinous rice cake, brown sugar, roasted soybean flour'),
        D3('冰粉', '¥18', '冰粉、红糖水、山楂、葡萄干', en='Ice jelly dessert', kw='ice jelly, brown sugar syrup, hawthorn, raisins'),
    ]),
])

# ---------------------------------------------------------------- M43 Ethiopian (en, clean)
menu(id='M43', title='Lalibela Table', lang='en', font='gill', bg='white', style='clean', heldout=True, sections=[
    ('Wats and raw', [
        D3('Doro Wat', 'ETB 450', 'chicken simmered with berbere and onion, niter kibbeh, one boiled egg, injera'),
        D3('Kitfo', 'ETB 520', 'minced beef seasoned with mitmita and niter kibbeh, ayib fresh cheese, injera'),
        D3('Tibs', 'ETB 480', 'beef cubes sauteed with onion, jalapeno and rosemary'),
        D3('Misir Wat', 'ETB 300', 'red lentils simmered with berbere and garlic'),
        D3('Gomen', 'ETB 280', 'collard greens with garlic and ginger'),
        D3('Dulet', 'ETB 430', 'minced tripe and beef sauteed with onion, mitmita and spiced butter'),
    ]),
    ('Platters, bread and drinks', [
        D3('Yebeyaynetu Veggie Platter', 'ETB 400', 'lentils, collard greens, cabbage and carrot, tomato salad, injera'),
        D3('Dabo', 'ETB 120', 'spiced honey bread, served warm'),
        D3('Sambusa', 'ETB 150', 'fried pastry triangles filled with spiced lentils and green chili'),
        D3("Chef's Wat of the Day", 'ETB 380', 'ask your server', *S()),
        D3('Spris', 'ETB 140', 'layered fresh avocado, mango and papaya juice'),
        D3('Buna', 'ETB 90', 'roasted coffee served ceremony style'),
    ]),
])

# ---------------------------------------------------------------- M44 Turkish grill (en, blur)
menu(id='M44', title='Ocakbasi Karadeniz', lang='en', font='trebuchet', bg='white', style='blur', heldout=True, sections=[
    ('From the grill and oven', [
        D3('Lamb Shish Kebab', 'TL 420', 'cubed lamb marinated with onion and pepper, grilled over charcoal, grilled tomato'),
        D3('Iskender Kebab', 'TL 480', 'sliced doner lamb on pita bread, hot tomato sauce, melted butter, yogurt on the side'),
        D3('Lahmacun', 'TL 220', 'thin dough topped with minced lamb, tomato, parsley and lemon'),
        D3('Peynirli Pide', 'TL 260', 'boat-shaped baked dough filled with melted kashar cheese'),
        D3('Kofte Plate', 'TL 380', 'grilled beef meatballs, rice pilaf, grilled pepper, tomato'),
        D3("Chef's Mixed Grill of the Day", 'TL 520', 'ask your server', *S()),
    ]),
    ('Meze, soup, sweets', [
        D3('Mercimek Corbasi', 'TL 120', 'red lentil soup with lemon'),
        D3('Coban Salatasi', 'TL 130', 'tomato, cucumber, onion, parsley, olive oil'),
        D3('Ezme', 'TL 140', 'spicy tomato and pepper relish with walnuts and pomegranate molasses'),
        D3('Kunefe', 'TL 240', 'shredded pastry, melted Hatay cheese, sugar syrup, crushed pistachio'),
        D3('Sutlac', 'TL 150', 'baked rice pudding with milk'),
        D3('Cay', 'TL 40', 'Turkish black tea in a tulip glass'),
    ]),
])

# ---------------------------------------------------------------- M45 German beer hall (de, scan)
menu(id='M45', title='Zum Goldenen Hirsch', lang='de', font='times', bg='white', style='scan', heldout=True, sections=[
    ('Vom Grill und aus der Pfanne', [
        D3('Wiener Schnitzel', '€ 19', 'paniertes Kalbsschnitzel mit Semmelbröseln, Zitrone, Kartoffelsalat', en='Breaded veal cutlet', kw='breaded veal cutlet with bread crumbs, lemon, potato salad',
           *[Q('EGG', 'a public source says the cutlet is rolled in flour, whipped eggs and bread crumbs', 'WP_SCHNITZ')]),
        D3('Currywurst', '€ 11', 'gegrillte Bratwurst, Currysoße, Pommes', en='Curry sausage with fries', kw='grilled bratwurst sausage, curry ketchup sauce, fries'),
        D3('Weißwurst mit Brezel', '€ 10', 'zwei Weißwürste, süßer Senf, Brezel', en='White sausage with pretzel', kw='two white veal sausages, sweet mustard, pretzel'),
        D3('Schweinshaxe', '€ 22', 'knusprige Schweinshaxe, Dunkelbiersoße, Knödel', en='Roast pork knuckle', kw='crispy pork knuckle, dark beer sauce, dumpling'),
        D3('Rinderroulade', '€ 21', 'Rinderroulade mit Senf, Speck und Gurke, Rotkohl', en='Beef roulade', kw='beef roulade with mustard, bacon and pickle, red cabbage'),
        D3('Kartoffelsalat', '€ 6', 'warmer Kartoffelsalat mit Essig und Zwiebeln', en='Warm vinegar potatoes with onion', kw='warm potato salad with vinegar and onions'),
    ]),
    ('Brotzeit und Süßes', [
        D3('Obatzda mit Brezn', '€ 9', 'Camembert-Käsecreme mit Zwiebeln, Brezn', en='Cheese spread with pretzel', kw='camembert cheese spread with onions, pretzel'),
        D3('Käsespätzle', '€ 14', 'Spätzle mit Bergkäse und Röstzwiebeln', en='Cheese spaetzle', kw='spaetzle noodles with mountain cheese and fried onions',
           *[A('EGG', 'a public source says spaetzle dough is principally eggs, flour and salt', 'WP_SPAETZ'), A('WHE', 'spaetzle dough is made of flour', 'WP_SPAETZ')]),
        D3('Apfelstrudel', '€ 8', 'Apfelstrudel mit Vanillesoße', en='Apple strudel', kw='apple strudel with vanilla sauce'),
        D3('Schwarzwälder Kirschtorte', '€ 8', 'Kirschen, Schokolade, Sahne, Kirschwasser', en='Black Forest cake', kw='cherries, chocolate, whipped cream, kirsch'),
        D3('Tagesgericht des Hauses', '€ 16', 'bitte Servicepersonal fragen', *S(), en='Dish chosen by the house today'),
        D3('Apfelschorle', '€ 4', 'Apfelsaft mit Sprudelwasser', en='Apple juice spritzer', kw='apple juice with sparkling water'),
    ]),
])

# ---------------------------------------------------------------- M46 Brazilian churrascaria and bakery (pt, photo)
menu(id='M46', title='Churrascaria Estrela do Sul', lang='pt', font='verdana', bg='kraft', style='photo', heldout=True, sections=[
    ('Da brasa e da panela', [
        D3('Picanha na Brasa', 'R$ 78', 'picanha grelhada, farofa, vinagrete, arroz', en='Grilled picanha', kw='grilled picanha beef cap, toasted cassava flour, tomato vinaigrette, rice'),
        D3('Feijoada Completa', 'R$ 62', 'feijão preto, carne de porco, linguiça, couve, laranja', en='Black bean and pork feijoada', kw='black beans, pork, smoked sausage, collard greens, orange'),
        D3('Moqueca de Peixe', 'R$ 84', 'peixe branco, tomate, pimentão, leite de coco, dendê', en='Fish moqueca', kw='white fish, tomato, bell pepper, coconut milk, palm oil'),
        D3('Coxinha de Frango', 'R$ 12', 'massa recheada com frango, empanada e frita', en='Chicken coxinha', kw='dough filled with chicken, breaded and fried',
           *[A('WHE', 'a public source says the coxinha dough is made with wheat flour', 'WP_COXIN')]),
        D3('Acarajé com Camarão', 'R$ 36', 'bolinho de feijão-fradinho frito, camarão, salada', en='Black-eyed pea fritter with shrimp', kw='fried black-eyed pea fritter, shrimp, salad'),
        D3('Corte Especial do Dia', 'R$ 90', 'pergunte ao garçom', *S(), en='Grill master cut for today'),
    ]),
    ('Padaria e sobremesas', [
        D3('Pão de Queijo', 'R$ 14', 'bolinhas de queijo e polvilho', en='Cheese bread', kw='cheese bread balls with tapioca starch',
           *[A('EGG', 'a public source says pao de queijo is made with eggs, milk and cheese', 'WP_PDQ')]),
        D3('Pão Francês na Chapa', 'R$ 10', 'pãozinho francês tostado com manteiga', en='Toasted French bread roll with butter', kw='French bread roll toasted with butter'),
        D3('Brigadeiro', 'R$ 8', 'docinho de leite condensado, chocolate e manteiga', en='Chocolate fudge truffle', kw='sweet of condensed milk, chocolate and butter'),
        D3('Pudim de Leite', 'R$ 16', 'leite condensado, ovos e calda de caramelo', en='Milk pudding', kw='condensed milk, eggs and caramel sauce'),
        D3('Salada de Palmito', 'R$ 28', 'palmito, tomate, cebola, azeite', en='Hearts of palm salad', kw='hearts of palm, tomato, onion, olive oil'),
        D3('Suco de Maracujá', 'R$ 12', 'maracujá fresco e água', en='Passion fruit juice', kw='fresh passion fruit and water'),
    ]),
])

# ---------------------------------------------------------------- M47 Filipino (en, clean)
menu(id='M47', title='Lola Remy Kainan', lang='en', font='palatino', bg='cream', style='clean', heldout=True, sections=[
    ('Ulam and noodles', [
        D3('Chicken Adobo', 'PHP 320', 'chicken braised in soy sauce, vinegar, garlic and bay leaf, steamed rice'),
        D3('Pork Sinigang', 'PHP 360', 'tamarind broth, pork ribs, water spinach, radish'),
        D3('Kare-Kare', 'PHP 480', 'oxtail and vegetables in peanut sauce, bagoong alamang (shrimp paste) on the side'),
        D3('Pancit Canton', 'PHP 280', 'stir-fried wheat noodles, chicken, cabbage, carrot, soy sauce'),
        D3('Lumpiang Shanghai', 'PHP 240', 'crispy pork spring rolls, sweet chili sauce'),
        D3("Chef's Ulam of the Day", 'PHP 350', 'ask your server', *S()),
    ]),
    ('From the grill, sweets and drinks', [
        D3('Sisig', 'PHP 390', 'chopped pork cheek and onion on a hot plate, calamansi, topped with a fried egg'),
        D3('Crispy Pata', 'PHP 650', 'deep-fried pork knuckle, soy-vinegar dipping sauce'),
        D3('Bibingka', 'PHP 160', 'rice cake baked in banana leaf with salted egg, cheese and grated coconut'),
        D3('Turon', 'PHP 120', 'banana and jackfruit in a spring roll wrapper, caramelized sugar',
           A('WHE', 'the spring roll wrapper is made of wheat flour', 'BASIC')),
        D3('Halo-Halo', 'PHP 220', 'shaved ice, sweet beans, jelly, leche flan, ube ice cream, evaporated milk'),
        D3('Calamansi Juice', 'PHP 90', 'fresh calamansi, water, sugar'),
    ]),
])

# ---------------------------------------------------------------- M48 Italian-American pizzeria (en, scan)
menu(id='M48', title="Sal's Slice House", lang='en', font='rockwell', bg='cream', style='scan', heldout=True, sections=[
    ('Pies and subs', [
        D3('Pepperoni Pizza', '$18', 'tomato sauce, mozzarella, pepperoni'),
        D3('White Pie', '$19', 'ricotta, mozzarella, roasted garlic, olive oil'),
        D3('Chicken Parm Sub', '$14', 'breaded chicken cutlet, marinara, mozzarella, toasted sub roll'),
        D3('Meatball Sub', '$13', 'beef and pork meatballs, marinara, melted provolone cheese, hoagie roll'),
        D3('Chicken Caesar Wrap', '$12', 'grilled chicken, romaine, Caesar, flour tortilla wrap',
           A('WHE', 'a flour tortilla wrap is made of wheat flour', 'BASIC')),
        D3('Slice of the Day', '$5', 'ask at the counter', *S()),
    ]),
    ('Sides and sweets', [
        D3('Garlic Breadsticks', '$7', 'baked breadsticks brushed with olive oil, garlic and parsley'),
        D3('Baked Ziti', '$15', 'ziti baked with ricotta, marinara and mozzarella'),
        D3('Buffalo Wings', '$13', 'fried wings tossed in buffalo hot sauce, blue cheese dip, celery'),
        D3('Sicilian Tomato Salad', '$9', 'sliced tomato, red onion, basil, olive oil'),
        D3('New York Cheesecake', '$8', 'cream cheese filling, graham cracker crust'),
        D3('Fresh Lemonade', '$4', 'lemon juice, water, sugar'),
    ]),
])

apply_rules()
_used = {f[3] for m in MENUS4 for _, ds in m['sections'] for d in ds for f in d['facts']}
M.SOURCES.update({k: v for k, v in SOURCES4.items() if k in _used})
