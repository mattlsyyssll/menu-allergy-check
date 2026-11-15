"""Menu content and allergen facts for HELD-OUT SET 5 (M49-M56). Pure data plus one rule engine; uses the helpers of the frozen tools/menus_data.py.

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
W5 = 'fetched 2026-11-14 (page-fetch summary, set 5)'
WP = 'https://en.wikipedia.org/wiki/'
FARE = 'https://www.foodallergy.org/living-food-allergies/food-allergy-essentials/common-allergens/'
SOURCES5 = {
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
    'WP_PATTY': ('Wikipedia, Jamaican patty: the "flaky shell" is "often tinted golden yellow with an egg yolk mixture, annatto or turmeric"; traditionally filled with seasoned ground beef', WP + 'Jamaican_patty', W5),
    'WP_KHACH': ('Wikipedia, Khachapuri: Adjaruli is "boat-shaped khachapuri, with cheese, butter, and an egg yolk in the middle"', WP + 'Khachapuri', W5),
    'WP_MALA': ('Wikipedia, Malasada: main ingredients are wheat flour, sugar, eggs, milk and yeast', WP + 'Malasada', W5),
    'WP_MOMO': ('Wikipedia, Momo (food): wrapper is a "simple white-flour-and-water dough"; in Nepal momos are often served with achar, which may be sesame-, peanut- or soybean-based, or with a tomato chutney', WP + 'Momo_(food)', W5),
    'WP_LOCO': ('Wikipedia, Loco moco: "white rice, topped with a hamburger patty and brown gravy, and a sunny-side-up fried egg"', WP + 'Loco_moco', W5),
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
    # achar: WP_MOMO (named dipping sauce)
    ('PEA', r'\bachar\b', 'a public source says achar may be peanut-based', 'WP_MOMO'),
    ('SES', r'\bachar\b', 'a public source says achar may be sesame-based', 'WP_MOMO'),
    ('SOY', r'\bachar\b', 'a public source says achar may be soybean-based', 'WP_MOMO'),
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

MENUS5 = []


def D3(name, price, desc='', *facts, sub='', en='', kw=''):
    fl = []
    for f in facts:
        if isinstance(f, En):
            en = str(f)
        else:
            fl.append(f)
    return {'name': name, 'price': price, 'desc': desc, 'facts': fl, 'sub': sub, 'en': en, 'kw': kw}


def menu(**kw):
    MENUS5.append(kw)


def dish_text(d):
    return ' '.join(x for x in (d['name'], d['sub'], d['desc'], d['en'], d['kw']) if x).lower()


def special(d):
    return len({f[0] for f in d['facts']}) == len(M.ALLERGENS)


def apply_rules():
    for m in MENUS5:
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
    for m in MENUS5:
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


# colsplit = how many sections go into each column (renderer in make_set5.py); layout 1 col = [n]
# ---------------------------------------------------------------- M49 Jamaican (en, glare, two columns)
menu(id='M49', title='Blue Mountain Cookshop', lang='en', font='georgia', bg='cream', style='glare', heldout=True, colsplit=[1, 1], sections=[
    ('From the pot and the pit', [
        D3('Jerk Chicken Quarter', 'J$2,400', 'leg quarter smoked over pimento wood with scotch bonnet and allspice, rice and peas, fried plantain'),
        D3('Curry Goat', 'J$2,800', 'goat slow-cooked with curry powder, potato, thyme and scallion, white rice'),
        D3('Ackee and Saltfish', 'J$2,600', 'ackee sauteed with salted cod, onion, tomato and thyme, boiled green banana'),
        D3('Escovitch Snapper', 'J$3,600', 'fried whole snapper topped with pickled onion, carrot and scotch bonnet, bammy'),
        D3('Oxtail Stew', 'J$3,800', 'oxtail slow-braised with lima beans, carrot and allspice, white rice'),
        D3("Cook's Special Pot", 'J$2,500', 'ask your server', *S()),
    ]),
    ('Patties, sides and sweets', [
        D3('Beef Patty', 'J$700', 'flaky turmeric pastry filled with spiced ground beef and scotch bonnet',
           Q('EGG', 'a public source says the patty shell is often tinted with an egg yolk mixture', 'WP_PATTY')),
        D3('Red Peas Soup', 'J$1,400', 'red kidney beans, pumpkin, yam and carrot with spinners (dumplings)'),
        D3('Steamed Callaloo', 'J$900', 'callaloo greens steamed with onion, tomato and thyme'),
        D3('Gizzada', 'J$500', 'tart shell filled with spiced grated coconut and brown sugar'),
        D3('Peanut Punch', 'J$800', 'chilled blend of roasted peanuts, milk, nutmeg and oats'),
        D3('Sorrel Drink', 'J$600', 'chilled hibiscus sorrel steeped with ginger and cloves'),
    ]),
])

# ---------------------------------------------------------------- M50 Georgian (en, clean, one column, three headings)
menu(id='M50', title='Supra Tbilisi', lang='en', font='baskerville', bg='white', style='clean', heldout=True, colsplit=[3], sections=[
    ('Bread and starters', [
        D3('Adjaruli Khachapuri', 'GEL 24', 'boat-shaped bread filled with melted sulguni cheese, butter and a runny egg yolk',
           Q('EGG', 'a public source names an egg yolk in Adjaruli khachapuri', 'WP_KHACH')),
        D3('Pkhali', 'GEL 16', 'chopped spinach with walnut paste, garlic, coriander and pomegranate seeds'),
        D3('Lobiani', 'GEL 18', 'baked bread stuffed with spiced red beans and onion'),
    ]),
    ('From the clay pot and the grill', [
        D3('Chakhokhbili', 'GEL 32', 'chicken stewed with tomato, onion, herbs and garlic'),
        D3('Mtsvadi', 'GEL 36', 'charcoal-grilled pork skewers with red onion and tkemali plum sauce'),
        D3('Khinkali', 'GEL 28', 'twisted dumplings filled with spiced beef and pork, hot broth inside'),
        D3('Kupati', 'GEL 30', 'spiced pork sausages pan-fried with onion and pomegranate'),
        D3("Supra Master's Choice", 'GEL 38', 'ask your server', *S()),
    ]),
    ('Salads, sweets and drinks', [
        D3('Tomato Salad with Sunflower Oil', 'GEL 14', 'tomato, cucumber, red onion and basil dressed with sunflower oil'),
        D3('Churchkhela', 'GEL 12', 'string of walnuts dipped in thickened grape juice'),
        D3('Fig and Pear Plate', 'GEL 15', 'fresh figs and pears with mint'),
        D3('Tarkhuna Lemonade', 'GEL 9', 'tarragon, sugar, lemon and sparkling water'),
    ]),
])

# ---------------------------------------------------------------- M51 Nepalese momo house (en, scan, two columns)
menu(id='M51', title='Himal Momo House', lang='en', font='trebuchet', bg='cream', style='scan', heldout=True, colsplit=[1, 1], sections=[
    ('Momo and noodles', [
        D3('Steamed Chicken Momo', 'NPR 320', 'steamed dumplings of spiced chicken, ginger and cilantro, served with achar dipping sauce',
           Q('WHE', 'a public source says the momo wrapper is a white-flour dough', 'WP_MOMO')),
        D3('Jhol Momo', 'NPR 360', 'dumplings of spiced vegetables in a warm sesame and tomato broth'),
        D3('Pan-Fried Buff Momo', 'NPR 380', 'pan-fried dumplings of water buffalo and scallion, tomato dip'),
        D3('Veg Thukpa', 'NPR 300', 'hand-pulled wheat noodle soup with carrot, cabbage and greens'),
        D3("House Momo Special", 'NPR 340', 'ask your server', *S()),
    ]),
    ('Curries, sides and drinks', [
        D3('Dal Bhat', 'NPR 420', 'lentil soup, steamed rice, seasonal greens and cucumber pickle'),
        D3('Chicken Sekuwa', 'NPR 450', 'charcoal-grilled marinated chicken with timur pepper and lime'),
        D3('Aloo Tama', 'NPR 280', 'potato and bamboo shoot curry with fenugreek'),
        D3('Sel Roti', 'NPR 120', 'fried ring of ground rice, sugar and cardamom'),
        D3('Peanut Sadheko', 'NPR 200', 'roasted peanuts tossed with onion, tomato, green chili and lime'),
        D3('Juju Dhau', 'NPR 180', 'sweet yogurt dessert from Bhaktapur, served in a clay pot'),
        D3('Masala Chiya', 'NPR 90', 'black tea simmered with milk, cardamom and ginger'),
    ]),
])

# ---------------------------------------------------------------- M52 Hawaiian plate lunch (en, blur, two columns)
menu(id='M52', title="Ono Kau Kau Plate House", lang='en', font='arialr', bg='white', style='blur', heldout=True, colsplit=[1, 1], sections=[
    ('Plate lunches', [
        D3('Loco Moco', '$16', 'two scoops rice topped with a hamburger patty, brown gravy and a fried egg'),
        D3('Kalua Pork Plate', '$17', 'smoked shredded pork with cabbage, two scoops rice, macaroni salad with mayonnaise'),
        D3('Kahuku Shrimp Plate', '$20', 'shell-on shrimp sauteed in garlic butter, two scoops rice, green salad'),
        D3('Teriyaki Beef Plate', '$18', 'grilled beef in a teriyaki glaze of soy sauce, ginger and brown sugar, two scoops rice'),
        D3('Ahi Poke Bowl', '$19', 'raw ahi tuna with shoyu, sesame oil, sweet onion and seaweed over rice'),
        D3("Today's Plate Special", '$17', 'ask at the counter', *S()),
    ]),
    ('Sides, sweets and drinks', [
        D3('Spam Musubi', '$5', 'grilled Spam glazed with soy sauce on pressed rice, wrapped in nori'),
        D3('Chicken Long Rice', '$8', 'soup of chicken, mung bean noodles, ginger and scallion'),
        D3('Haupia', '$5', 'chilled squares of coconut milk and sugar set with cornstarch'),
        D3('Malasadas', '$7', 'three fried dough balls rolled in sugar',
           A('EGG', 'a public source lists eggs as a main ingredient of malasada dough', 'WP_MALA'),
           A('MIL', 'a public source lists milk as a main ingredient of malasada dough', 'WP_MALA')),
        D3('Macadamia Pancakes', '$12', 'buttermilk pancakes with toasted macadamia nuts and coconut syrup'),
        D3('POG Juice', '$4', 'passion fruit, orange and guava juice over ice'),
    ]),
])

# ---------------------------------------------------------------- M53 Mexican panaderia and cafe (es, photo, one column, three headings)
menu(id='M53', title='Panadería La Concha Dorada', lang='es', font='cochin', bg='kraft', style='photo', heldout=True, colsplit=[3], sections=[
    ('Pan dulce', [
        D3('Concha de Vainilla', '$28', 'pan dulce con cubierta crujiente de azúcar', en='Vanilla sweet bread', kw='sweet bread with a crisp sugar shell'),
        D3('Empanada de Cajeta', '$32', 'empanada de masa horneada rellena de cajeta de cabra y nuez pecana', en='Goat milk caramel turnover',
           kw='baked dough turnover filled with goat milk caramel and pecans'),
        D3('Polvorones', '$26', 'galletas de mantequilla con nuez', en='Butter shortbread', kw='butter cookies with pecans'),
    ]),
    ('Antojitos y comida', [
        D3('Torta de Jamón', '$75', 'jamón, frijoles y aguacate en telera', en='Ham sandwich', kw='ham, beans and avocado on a telera roll'),
        D3('Sope de Chorizo', '$65', 'sope de masa con chorizo, frijoles y queso fresco', en='Thick corn sope with chorizo',
           kw='thick corn masa disk with chorizo sausage, beans and fresh cheese'),
        D3('Quesadilla de Flor de Calabaza', '$70', 'tortilla de maíz con queso Oaxaca y flor de calabaza', en='Squash blossom quesadilla',
           kw='corn tortilla with Oaxaca cheese and squash blossom'),
        D3('Sopa de Lima', '$68', 'caldo de pollo con lima y tiras de tortilla', en='Lime and chicken soup', kw='chicken broth with lime and tortilla strips'),
        D3('Ensalada de Jícama', '$55', 'jícama, naranja y pepino con chile y limón', en='Jicama salad', kw='jicama, orange and cucumber with chili and lime'),
        D3('Antojito del Día', '$70', 'pregunte al mesero', *S(), en='Snack of the day'),
    ]),
    ('Café y bebidas', [
        D3('Café de Olla', '$30', 'café con piloncillo y canela', en='Spiced clay-pot coffee', kw='coffee with raw cane sugar and cinnamon'),
        D3('Champurrado', '$38', 'bebida espesa de masa, chocolate y piloncillo', en='Thick chocolate masa drink', kw='thick masa drink with chocolate and raw cane sugar'),
        D3('Agua de Tamarindo', '$28', 'agua fresca de tamarindo', en='Tamarind fresh water', kw='fresh tamarind water'),
    ]),
])

# ---------------------------------------------------------------- M54 French creperie (fr, clean, two columns, four headings)
menu(id='M54', title='Crêperie Le Moulin Breton', lang='fr', font='palatino', bg='white', style='clean', heldout=True, colsplit=[2, 2], sections=[
    ('Galettes salées', [
        D3('Galette Complète', '€ 11', 'galette de sarrasin, jambon, emmental, œuf', en='Ham, cheese and egg buckwheat galette',
           kw='buckwheat galette with ham, Emmental cheese and egg'),
        D3('Galette Forestière', '€ 12', 'galette de sarrasin, champignons, crème', en='Mushroom buckwheat galette',
           kw='buckwheat galette with mushrooms and sour cream'),
        D3('Galette du Jour', '€ 13', 'demandez au serveur', *S(), en='Galette of the day'),
    ]),
    ('Crêpes sucrées', [
        D3('Crêpe Beurre-Sucre', '€ 5', 'crêpe au beurre salé et sucre', en='Salted butter and sugar crepe', kw='thin wheat crepe with salted butter and sugar'),
        D3('Crêpe Suzette', '€ 9', 'crêpe flambée au Grand Marnier, sauce orange et beurre', en='Flamed orange crepe',
           kw='thin wheat crepe flamed with Grand Marnier in orange butter sauce'),
        D3('Crêpe Chocolat-Noisette', '€ 8', 'crêpe au chocolat et noisettes grillées', en='Chocolate hazelnut crepe',
           kw='thin wheat crepe with chocolate and toasted hazelnuts'),
        D3('Crêpe Citron', '€ 5', 'crêpe au citron et sucre', en='Lemon sugar crepe', kw='thin wheat crepe with lemon and sugar'),
    ]),
    ('Salades et soupes', [
        D3('Salade de Chèvre Chaud', '€ 12', 'chèvre chaud sur toasts, miel et noix', en='Warm goat cheese salad',
           kw='warm goat cheese on toasted bread with honey and walnuts'),
        D3('Soupe de Poisson', '€ 9', 'soupe de poisson, rouille et croûtons', en='Fish soup',
           kw='fish soup with rouille (garlic mayonnaise) and toasted bread croutons'),
        D3('Salade de Lentilles', '€ 8', 'lentilles vertes, échalotes, vinaigrette à la moutarde', en='Green lentil salad',
           kw='green lentils, shallots, mustard vinaigrette'),
    ]),
    ('Boissons', [
        D3('Cidre Breton', '€ 5', 'cidre brut ou doux, servi en bolée', en='Breton cider', kw='dry or sweet apple cider served in a ceramic bowl cup'),
        D3('Chocolat Chaud', '€ 5', 'chocolat chaud au lait', en='Hot chocolate', kw='hot chocolate made with milk'),
    ]),
])

# ---------------------------------------------------------------- M55 Italian pasticceria and gelateria (it, glare, two columns, three headings)
menu(id='M55', title='Pasticceria Rossi e Figli', lang='it', font='optima', bg='cream', style='glare', heldout=True, colsplit=[2, 1], sections=[
    ('Dolci', [
        D3('Sfogliatella Riccia', '€ 3,50', 'sfoglia croccante ripiena di ricotta, semolino e scorza d\'arancia', en='Crisp layered ricotta pastry',
           kw='crisp layered pastry filled with ricotta, semolina and orange zest'),
        D3('Baba al Rum', '€ 3,00', 'dolce lievitato imbevuto di sciroppo al rum', en='Rum-soaked baba', kw='rum-soaked yeast cake'),
        D3('Torta della Nonna', '€ 4,00', 'crema pasticcera e pinoli in crosta di frolla', en="Grandma's tart", kw='tart with custard cream and pine nuts'),
        D3('Cantucci', '€ 3,50', 'biscotti croccanti alle mandorle', en='Twice-baked almond biscuits', kw='crunchy twice-baked almond cookies'),
        D3('Dolce del Giorno', '€ 4,00', 'chiedere al banco', *S(), en='Sweet of the day'),
    ]),
    ('Gelato e granite', [
        D3('Gelato Fior di Latte', '€ 3,50', 'gelato al latte fresco e panna', en='Milk and cream gelato', kw='fresh milk and cream gelato'),
        D3('Granita al Limone', '€ 3,00', 'granita di limone siciliano', en='Lemon granita', kw='Sicilian lemon ice, shaved and sweetened'),
        D3('Sorbetto di Fragola', '€ 3,00', 'sorbetto di fragole fresche', en='Strawberry sorbet', kw='strawberry sorbet'),
        D3('Gusto del Giorno', '€ 3,50', 'chiedere al banco', *S(), en='Gelato flavor of the day'),
    ]),
    ('Salati e caffè', [
        D3('Pizza al Taglio', '€ 4,00', 'pizza rettangolare con pomodoro e origano', en='Pizza by the slice', kw='rectangular pizza slice with tomato and oregano'),
        D3('Panino alla Mortadella', '€ 6,00', 'panino con mortadella e granella di pistacchio', en='Mortadella sandwich', kw='sandwich roll with mortadella and crushed pistachio'),
        D3("Spremuta d'Arancia", '€ 4,50', 'arance rosse spremute', en='Fresh blood orange juice', kw='freshly squeezed blood orange juice'),
    ]),
])

# ---------------------------------------------------------------- M56 Taiwanese night market (zh Traditional Chinese, photo, two columns)
menu(id='M56', title='阿財夜市小吃', lang='zh', font='unicode', bg='cream', style='photo', heldout=True, colsplit=[1, 1], sections=[
    ('小吃', [
        D3('滷肉飯', 'NT$60', '滷豬五花、醬油、紅蔥頭、白飯', en='Braised pork rice', kw='braised minced pork belly, soy sauce, fried shallots, steamed rice'),
        D3('鹽酥雞', 'NT$80', '酥炸雞塊、九層塔、胡椒', en='Salt and pepper chicken bites', kw='fried chicken bites in sweet potato starch coating with fried basil and white pepper'),
        D3('大腸包小腸', 'NT$75', '烤香腸夾糯米腸、小黃瓜、蒜片', en='Sausage in a sticky rice sausage', kw='grilled pork sausage inside a sticky rice sausage with pickled cucumber and garlic'),
        D3('臭豆腐', 'NT$70', '炸臭豆腐、泡菜、辣椒醬', en='Fried stinky tofu', kw='fried stinky tofu with pickled cabbage and chili sauce'),
        D3('蔥抓餅', 'NT$45', '手抓麵餅、青蔥、雞蛋', en='Flaky scallion pancake', kw='flaky pan-fried wheat scallion pancake with egg'),
        D3('今日限定小吃', 'NT$65', '請詢問店員', *S(), en="Today's limited snack"),
    ]),
    ('湯、甜點與飲料', [
        D3('魚丸湯', 'NT$50', '魚丸、芹菜、油蔥酥', en='Fish ball soup', kw='fish ball soup with celery and fried shallots'),
        D3('花生捲冰淇淋', 'NT$65', '花生糖粉、薄餅皮、冰淇淋、香菜', en='Peanut brittle ice cream wrap',
           kw='shaved peanut brittle and two scoops of ice cream wrapped in a thin wheat crepe with cilantro'),
        D3('豆花', 'NT$45', '嫩豆腐、薑汁糖水、花生', en='Soft tofu dessert', kw='soft silken tofu dessert with ginger syrup and peanuts'),
        D3('地瓜球', 'NT$50', '炸地瓜、糖粉', en='Fried sweet potato balls', kw='fried chewy sweet potato balls dusted with sugar'),
        D3('珍珠奶茶', 'NT$55', '紅茶、牛奶、粉圓', en='Pearl milk tea', kw='black tea, milk and tapioca pearls'),
        D3('愛玉檸檬', 'NT$50', '愛玉凍、檸檬汁、蜂蜜', en='Aiyu jelly lemonade', kw='aiyu jelly with lemon juice and honey'),
    ]),
])

apply_rules()
_used = {f[3] for m in MENUS5 for _, ds in m['sections'] for d in ds for f in d['facts']}
M.SOURCES.update({k: v for k, v in SOURCES5.items() if k in _used})
