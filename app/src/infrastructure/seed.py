import json
import logging
from datetime import datetime
from src.core.config import settings
from src.core.security import hash_password
from src.infrastructure.database import get_raw_connection, transaction

logger = logging.getLogger("marea.seed")

CATEGORIES_SEED = [
    {"name": "Tortas y pasteles", "slug": "tortas", "description": "Tortas artesanales para compartir grandes momentos", "display_order": 1},
    {"name": "Cupcakes", "slug": "cupcakes", "description": "Bocados esponjosos con decoraciones de autor", "display_order": 2},
    {"name": "Galletas artesanales", "slug": "galletas", "description": "Galletas horneadas diariamente con mantequilla pura", "display_order": 3},
    {"name": "Postres individuales", "slug": "postres-individuales", "description": "Porciones individuales para pequeños antojos diarios", "display_order": 4},
    {"name": "De temporada", "slug": "de-temporada", "description": "Creaciones especiales por fechas y temporadas festivas", "display_order": 5},
    {"name": "Pedidos personalizados", "slug": "personalizados", "description": "Diseños únicos adaptados a tu celebración", "display_order": 6},
]

PRODUCTS_SEED = [
    {
        "category_slug": "tortas",
        "name": "Torta de vainilla y frutos rojos",
        "slug": "torta-vainilla-frutos-rojos-12p",
        "description": "Bizcocho húmedo de vainilla de Madagascar relleno de coulis artesanal de frutos rojos y crema batida.",
        "price_cop": 98000,
        "servings": "12 porciones",
        "prep_time_hours": 24,
        "ingredients": "Harina de trigo fortificada, mantequilla pura, huevos frescos, vainilla natural, fresas, moras, arándanos, azúcar orgánica.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": "Destacado",
        "stock": 10,
        "is_featured": True,
        "image_url": "/assets/products/torta-frutos-rojos.webp"
    },
    {
        "category_slug": "tortas",
        "name": "Torta tres leches artesanal",
        "slug": "torta-tres-leches-artesanal-12p",
        "description": "Tradicional bizcochuelo esponjoso empapado en nuestra infusión especial de tres leches y merengue tostado.",
        "price_cop": 85000,
        "servings": "12 porciones",
        "prep_time_hours": 24,
        "ingredients": "Leche entera, leche condensada, crema de leche fresca, huevos, harina de trigo, canela ceilán, azúcar.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": "Popular",
        "stock": 15,
        "is_featured": True,
        "image_url": "/assets/products/torta-tres-leches.webp"
    },
    {
        "category_slug": "tortas",
        "name": "Torta de chocolate intenso",
        "slug": "torta-chocolate-intenso-12p",
        "description": "Intenso bizcocho con 70% cacao colombiano, capas de ganache sedoso y cobertura de chocolate brillante.",
        "price_cop": 92000,
        "servings": "12 porciones",
        "prep_time_hours": 24,
        "ingredients": "Cacao de origen 70%, mantequilla de campo, huevos, harina de trigo, crema de leche, avellanas tostadas.",
        "allergens": ["gluten", "lacteos", "huevo", "frutos_secos"],
        "badge": None,
        "stock": 8,
        "is_featured": False,
        "image_url": "/assets/products/torta-chocolate.webp"
    },
    {
        "category_slug": "tortas",
        "name": "Cheesecake de maracuyá",
        "slug": "cheesecake-maracuya-10p",
        "description": "Base crocante de galleta artesanal de canela con crema suave de queso horneada y glaseado cítrico de maracuyá.",
        "price_cop": 78000,
        "servings": "10 porciones",
        "prep_time_hours": 24,
        "ingredients": "Queso crema natural, pulpa de maracuyá fresca, galletas de mantequilla, huevos, azúcar blanca, crema.",
        "allergens": ["lacteos", "huevo", "gluten"],
        "badge": "Nuevo",
        "stock": 12,
        "is_featured": True,
        "image_url": "/assets/products/cheesecake-maracuya.webp"
    },
    {
        "category_slug": "cupcakes",
        "name": "Caja de 6 cupcakes surtidos",
        "slug": "caja-6-cupcakes-surtidos",
        "description": "Selección artesanal: 2 Red Velvet con crema de queso, 2 Chocolate con fudge y 2 Vainilla con buttercream.",
        "price_cop": 36000,
        "servings": "6 unidades",
        "prep_time_hours": 12,
        "ingredients": "Harina, mantequilla, cacao, queso crema, azúcar pulverizada, vainilla, colorante vegetal natural.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": "Popular",
        "stock": 20,
        "is_featured": True,
        "image_url": "/assets/products/cupcakes-caja.webp"
    },
    {
        "category_slug": "cupcakes",
        "name": "Cupcake red velvet individual",
        "slug": "cupcake-red-velvet-individual",
        "description": "Porción individual de esponjoso red velvet coronada con remolino de frosting de queso crema.",
        "price_cop": 7500,
        "servings": "1 unidad",
        "prep_time_hours": 12,
        "ingredients": "Harina de trigo, cacao, suero de leche, queso crema, mantequilla, extracto de vainilla.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": None,
        "stock": 25,
        "is_featured": False,
        "image_url": "/assets/products/cupcake-redvelvet.webp"
    },
    {
        "category_slug": "galletas",
        "name": "Galletas de mantequilla decoradas (caja de 12)",
        "slug": "galletas-mantequilla-decoradas-12",
        "description": "Galletas de mantequilla pura decoradas a mano con glaseado real y diseños florales marinos.",
        "price_cop": 42000,
        "servings": "12 unidades",
        "prep_time_hours": 18,
        "ingredients": "Mantequilla europea, harina pastelera, azúcar glas, clara de huevo pasteurizada, limón.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": None,
        "stock": 18,
        "is_featured": False,
        "image_url": "/assets/products/galletas-mantequilla.webp"
    },
    {
        "category_slug": "galletas",
        "name": "Galletas con chips de chocolate (caja de 6)",
        "slug": "galletas-chips-chocolate-6",
        "description": "Galletas doradas con centro suave y generosos trozos de chocolate semiamargo y escamas de sal marina.",
        "price_cop": 24000,
        "servings": "6 unidades",
        "prep_time_hours": 12,
        "ingredients": "Harina de trigo, chispas de chocolate 58%, mantequilla, azúcar morena, sal marina de Manaure.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": "Bajo stock",
        "stock": 3,
        "is_featured": False,
        "image_url": "/assets/products/galletas-chips.webp"
    },
    {
        "category_slug": "postres-individuales",
        "name": "Brownie con arequipe artesanal",
        "slug": "brownie-arequipe-artesanal",
        "description": "Brownie melcochudo de chocolate amargo relleno de abundante arequipe casero de olla.",
        "price_cop": 9500,
        "servings": "1 unidad",
        "prep_time_hours": 8,
        "ingredients": "Chocolate 65%, arequipe tradicional de leche entera, mantequilla, huevos, harina, nueces opcionales.",
        "allergens": ["lacteos", "huevo", "gluten"],
        "badge": None,
        "stock": 30,
        "is_featured": False,
        "image_url": "/assets/products/brownie-arequipe.webp"
    },
    {
        "category_slug": "postres-individuales",
        "name": "Tartaleta de limón merengada",
        "slug": "tartaleta-limon-merengada",
        "description": "Masa sableé crocante con curd de limón Tahití fresco y merengue suizo sopleteado al momento.",
        "price_cop": 11000,
        "servings": "1 unidad",
        "prep_time_hours": 12,
        "ingredients": "Limón fresco, mantequilla, yemas de huevo, azúcar, harina de trigo, claras para merengue.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": "Agotado",
        "stock": 0,
        "is_featured": False,
        "image_url": "/assets/products/tartaleta-limon.webp"
    },
    {
        "category_slug": "postres-individuales",
        "name": "Vaso de tiramisú tradicional",
        "slug": "vaso-tiramisu-tradicional",
        "description": "Capas de bizcochos savoiardi bañados en espresso colombiano, crema de queso mascarpone y cacao en polvo.",
        "price_cop": 12500,
        "servings": "1 unidad",
        "prep_time_hours": 8,
        "ingredients": "Queso mascarpone, café espresso, galletas savoiardi, licor amaretto (sin alcohol residual), cacao.",
        "allergens": ["gluten", "lacteos", "huevo"],
        "badge": None,
        "stock": 14,
        "is_featured": False,
        "image_url": "/assets/products/vaso-tiramisu.webp"
    },
    {
        "category_slug": "de-temporada",
        "name": "Torta navideña de frutos secos",
        "slug": "torta-navidena-frutos-secos-14p",
        "description": "Torta especiada de temporada macerada con ciruelas, uvas pasas, nueces pecanas, almendras y toque de ron.",
        "price_cop": 110000,
        "servings": "14 porciones",
        "prep_time_hours": 48,
        "ingredients": "Nueces pecanas, almendras, higos, uvas pasas, especias dulces (clavo, canela, nuez moscada), harina, mantequilla.",
        "allergens": ["gluten", "lacteos", "huevo", "frutos_secos"],
        "badge": "Temporada",
        "stock": 5,
        "is_featured": True,
        "image_url": "/assets/products/torta-navidena.webp"
    }
]

def seed_database():
    """Siembra los datos iniciales de demostración: Administrador, Categorías y 12 Productos."""
    conn = get_raw_connection()
    now_iso = datetime.now().isoformat()
    try:
        with transaction(conn, immediate=True):
            cursor = conn.cursor()
            
            # 1. Sembrar Administrador si no existe
            cursor.execute("SELECT id FROM users WHERE email = ?;", (settings.ADMIN_EMAIL,))
            if not cursor.fetchone():
                admin_pw_hash = hash_password(settings.ADMIN_PASSWORD)
                cursor.execute(
                    """
                    INSERT INTO users (email, full_name, phone, hashed_password, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'administrador', ?, ?);
                    """,
                    (settings.ADMIN_EMAIL, settings.ADMIN_NAME, "+57 300 123 4567", admin_pw_hash, now_iso, now_iso)
                )
                logger.info("Usuario administrador sembrado: %s", settings.ADMIN_EMAIL)
                
            # 2. Sembrar Categorías
            category_id_map = {}
            for cat in CATEGORIES_SEED:
                cursor.execute("SELECT id FROM categories WHERE slug = ?;", (cat["slug"],))
                row = cursor.fetchone()
                if row:
                    category_id_map[cat["slug"]] = row[0]
                else:
                    cursor.execute(
                        """
                        INSERT INTO categories (name, slug, description, display_order, is_active, created_at)
                        VALUES (?, ?, ?, ?, 1, ?);
                        """,
                        (cat["name"], cat["slug"], cat["description"], cat["display_order"], now_iso)
                    )
                    category_id_map[cat["slug"]] = cursor.lastrowid
                    
            logger.info("Categorías sembradas: %d", len(category_id_map))
            
            # 3. Sembrar Productos del Catálogo Oficial
            products_inserted = 0
            for prod in PRODUCTS_SEED:
                cat_id = category_id_map.get(prod["category_slug"])
                if not cat_id:
                    continue
                cursor.execute("SELECT id FROM products WHERE slug = ?;", (prod["slug"],))
                if not cursor.fetchone():
                    cursor.execute(
                        """
                        INSERT INTO products (
                            category_id, name, slug, description, price_cop, servings,
                            prep_time_hours, ingredients, allergens, image_url, badge,
                            stock, is_active, is_featured, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?);
                        """,
                        (
                            cat_id, prod["name"], prod["slug"], prod["description"],
                            prod["price_cop"], prod["servings"], prod["prep_time_hours"],
                            prod["ingredients"], json.dumps(prod["allergens"]),
                            prod["image_url"], prod["badge"], prod["stock"],
                            1 if prod["is_featured"] else 0, now_iso, now_iso
                        )
                    )
                    products_inserted += 1
                    
            if products_inserted > 0:
                logger.info("Productos del catálogo sembrados: %d productos", products_inserted)
    finally:
        conn.close()
