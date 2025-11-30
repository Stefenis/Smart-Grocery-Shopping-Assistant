import streamlit as st
from datetime import datetime, timedelta, date

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="Smart Grocery Assistant", page_icon="🛒", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #ffffff; }
        [data-testid="stSidebar"] { background-color: #f8f9fa; }
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, li, .stText { color: #212529 !important; }
        .stTextInput input, .stNumberInput input, .stDateInput input { color: #212529 !important; background-color: #ffffff !important; }
        div[data-baseweb="select"] > div { background-color: #ffffff !important; color: #212529 !important; }
        header {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden !important;}
        footer {visibility: hidden;}
        .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- MOCK DATABASES ---
HEALTH_DB = {
    "white flour": "almond flour",
    "salt": "herbs & spices",
    "jam": "mashed berries",
    "white sugar syrup": "maple syrup",
    "crispy fries": "air-fried fries",
    "whole milk": "low-fat milk",
    "cream": "coconut milk",
    "regular yogurt": "greek yogurt",
    "cheese slices": "low-fat cheese",
    "sausage": "lean chicken sausage",
    "white bread pizza base": "cauliflower crust",
    "regular noodles": "zoodles (zucchini noodles)",
    "mashed potatoes": "mashed cauliflower",
    "refined cereal": "oats",
    "granola bars": "nuts & seeds mix",
    "energy drinks": "electrolyte water",
    "milkshake": "protein smoothie",
    "pastries": "whole-grain muffins",
    "white tortilla": "whole wheat tortilla",
    "white pita": "whole-grain pita",
    "regular crackers": "whole-grain crackers",
    "pizza": "grilled veggie flatbread",
    "white gnocchi": "sweet potato gnocchi",
    "sugary coffee": "black coffee",
    "latte": "oat milk latte",
    "bbq marinade": "dry rub spices",
    "ketchup": "salsa",
    "chocolate spread": "peanut butter",
    "white potato": "sweet potato",
    "heavy gravy": "tomato-based sauce",
    "white couscous": "quinoa",
    "regular wrap": "lettuce wrap",
    "fried snacks": "air-fried snacks",
    "regular ice pops": "frozen fruit pops",
    "soft drinks": "infused water"
}


USAGE_RULES = {
    "milk": 7,
    "eggs": 14,
    "bread": 5,
    "apples": 10,
    "soda": 3
}

# --- SESSION STATE INITIALIZATION ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = [
        {"item": "Milk", "category": "Dairy", "buy_date": datetime.now(), "expiry_date": datetime.now() + timedelta(days=2), "quantity": 1, "unit": "L"},
        {"item": "Yogurt", "category": "Dairy", "buy_date": datetime.now() - timedelta(days=10), "expiry_date": datetime.now() - timedelta(days=1), "quantity": 2, "unit": "cups"}, 
        {"item": "Chicken", "category": "Meat", "buy_date": datetime.now() - timedelta(days=1), "expiry_date": datetime.now() + timedelta(days=4), "quantity": 1, "unit": "kg"},
        {"item": "White Bread", "category": "Bakery", "buy_date": datetime.now() - timedelta(days=1), "expiry_date": datetime.now() + timedelta(days=3), "quantity": 1, "unit": "loaf"},
    ]

if 'shopping_list' not in st.session_state:
    st.session_state.shopping_list = []

if 'history' not in st.session_state:
    st.session_state.history = [
        {"item": "Eggs", "last_bought": datetime.now() - timedelta(days=16)},
        {"item": "Bread", "last_bought": datetime.now() - timedelta(days=2)},
    ]

if 'out_of_stock' not in st.session_state:
    st.session_state.out_of_stock = []

# State for handling the Health Suggestion flow
if 'pending_item' not in st.session_state:
    st.session_state.pending_item = None

# --- HELPER FUNCTIONS ---
def add_to_list(item_data):
    """Adds an item dictionary to the shopping list if not already there."""
    # Convert date objects to datetime if necessary for consistency
    if isinstance(item_data['expiry_date'], date) and not isinstance(item_data['expiry_date'], datetime):
         item_data['expiry_date'] = datetime.combine(item_data['expiry_date'], datetime.min.time())

    for existing in st.session_state.shopping_list:
        if isinstance(existing, dict) and existing['item'] == item_data['item']:
            return False
    st.session_state.shopping_list.append(item_data)
    return True

def get_expiry_status(expiry_date):
    """Calculates days until expiry."""
    if isinstance(expiry_date, datetime):
        target = expiry_date
    else:
        target = datetime.combine(expiry_date, datetime.min.time())
    today = datetime.now()
    delta = target - today
    return delta.days

# --- SIDEBAR: ADD ITEM & SHOPPING LIST ---
with st.sidebar:
    st.header("➕ Add New Item")
    
    # We use a form to group inputs, preventing reload on every keystroke
    with st.form("add_item_form"):
        new_item = st.text_input("Item Name")
        new_category = st.selectbox("Category", ["General", "Dairy", "Meat", "Produce", "Bakery", "Snacks", "Beverages", "Household"])
        
        c1, c2 = st.columns(2)
        with c1:
            new_qty = st.number_input("Qty", min_value=1, value=1)
        with c2:
            new_unit = st.selectbox("Unit", ["pcs", "kg", "g", "L", "ml", "pkt", "box"])
        
        new_expiry = st.date_input("Expiry Date", value=datetime.now() + timedelta(days=7))
        
        # This button simply submits the form
        submitted = st.form_submit_button("Check & Add", type="primary")

    # Logic when form is submitted
    if submitted and new_item:
        suggestion = HEALTH_DB.get(new_item.lower())
        
        item_payload = {
            "item": new_item,
            "category": new_category,
            "quantity": new_qty,
            "unit": new_unit,
            "expiry_date": new_expiry
        }

        if suggestion:
            # Save to session state to handle the "Decision" UI outside the form
            st.session_state.pending_item = {
                "original": item_payload,
                "suggestion": suggestion
            }
            st.rerun() # Force rerun to show the decision UI below immediately
        else:
            # No suggestion, add directly
            if add_to_list(item_payload):
                st.success(f"Added {new_item}!")
            else:
                st.warning("Item already in list.")

    # --- HEALTH SUGGESTION MODAL (Simulated) ---
    # This sits outside the form so it persists based on session_state
    if st.session_state.pending_item:
        p_item = st.session_state.pending_item
        suggestion_name = p_item['suggestion']
        
        st.info(f"💡 **Health Tip:** **{suggestion_name.title()}** is healthier than **{p_item['original']['item']}**.")
        
        col_y, col_n = st.columns(2)
        
        # Option A: Take Suggestion
        if col_y.button(f"Use {suggestion_name.title()}", use_container_width=True):
            modified_item = p_item['original'].copy()
            modified_item['item'] = suggestion_name.title()
            add_to_list(modified_item)
            st.session_state.pending_item = None # Clear state
            st.rerun()

        # Option B: Keep Original
        if col_n.button(f"Keep {p_item['original']['item']}", use_container_width=True):
            add_to_list(p_item['original'])
            st.session_state.pending_item = None # Clear state
            st.rerun()

    st.markdown("---")
    
    # --- SHOPPING LIST ---
    st.subheader(f"🛒 Your Cart ({len(st.session_state.shopping_list)})")
    
    if st.session_state.shopping_list:
        for i, item_data in enumerate(st.session_state.shopping_list):
            c1, c2 = st.columns([5, 1])
            c1.text(f"{item_data['item']} ({item_data['quantity']}{item_data['unit']})")
            
            if c2.button("x", key=f"sidebar_del_{i}"):
                st.session_state.shopping_list.pop(i)
                st.rerun()
        
        if st.button("✅ Checkout", use_container_width=True):
            for item_data in st.session_state.shopping_list:
                # Ensure date format is compatible with inventory
                exp_date = item_data['expiry_date']
                if not isinstance(exp_date, datetime):
                     exp_date = datetime.combine(exp_date, datetime.min.time())

                st.session_state.inventory.append({
                    "item": item_data['item'],
                    "category": item_data.get('category', 'General'),
                    "buy_date": datetime.now(),
                    "expiry_date": exp_date,
                    "quantity": item_data['quantity'],
                    "unit": item_data['unit']
                })
            st.session_state.shopping_list = []
            st.balloons()
            st.rerun()
    else:
        st.caption("Cart is empty.")
    
    st.markdown("---")
    st.info("**Student Details:**\n\nReg No: [Your ID]\n\nName: [Your Name]")

# --- MAIN UI LAYOUT ---

st.title("🛒 Smart Grocery Shopping Assistant")
st.markdown("All your grocery needs in one place.")
st.markdown("---")

# ==========================================
# SECTION 1: TOP ROW (INVENTORY + EXPIRY)
# ==========================================

col_inv, col_alerts = st.columns([2, 1])

# --- LEFT: INVENTORY MANAGER ---
with col_inv:
    st.header("1. Digital Pantry Inventory")
    
    if st.session_state.inventory:
        c1, c2, c3, c4, c5 = st.columns([3, 1, 2, 2, 1])
        c1.markdown("**Item**")
        c2.markdown("**Qty**")
        c3.markdown("**Expiry Date**")
        c4.markdown("**Category**")
        c5.markdown("**Action**")
        st.markdown("---")
        
        for i, product in enumerate(st.session_state.inventory):
            c1, c2, c3, c4, c5 = st.columns([3, 1, 2, 2, 1])
            
            # Safe date formatting
            expiry_val = product['expiry_date']
            if isinstance(expiry_val, datetime):
                expiry_str = expiry_val.strftime('%Y-%m-%d')
            else:
                expiry_str = str(expiry_val)
            
            c1.write(product['item'])
            c2.write(f"{product['quantity']} {product['unit']}")
            c3.write(expiry_str)
            c4.write(product['category'])
            
            if c5.button("Remove", key=f"inv_rm_{i}"):
                if product['item'] not in st.session_state.out_of_stock:
                    st.session_state.out_of_stock.append(product['item'])
                st.session_state.inventory.pop(i)
                st.rerun()
    else:
        st.info("Pantry is empty.")

# --- RIGHT: EXPIRY ALERTS ---
with col_alerts:
    st.header("2. Alerts")
    st.subheader("⚠️ Expiry Status")
    
    alerts_found = False
    for product in st.session_state.inventory:
        expiry_val = product.get('expiry_date', datetime.now())
        days_left = get_expiry_status(expiry_val)
        
        if days_left < 0:
            st.error(f"❌ **{product['item']}** EXPIRED!")
            alerts_found = True
        elif days_left <= 3:
            st.warning(f"⏳ **{product['item']}** expires in {days_left + 1} days.")
            alerts_found = True

    if not alerts_found:
        st.success("✅ All items are fresh!")

st.markdown("---")

# ==========================================
# SECTION 2: BOTTOM ROW (INSIGHTS)
# ==========================================
st.header("3. Smart Insights")

col_dash_1, col_dash_2 = st.columns(2)

# --- LEFT COLUMN: SUGGESTIONS ---
with col_dash_1:
    st.subheader("🛒 Suggested Items")
    
    suggestions_found = False
    
    # 1. Recently Ran Out
    if st.session_state.out_of_stock:
        st.markdown("**Ran out recently:**")
        # Copy list to avoid modification issues during iteration
        for i, item_name in enumerate(list(st.session_state.out_of_stock)):
            suggestions_found = True
            c1, c2 = st.columns([3, 2])
            c1.write(f"• {item_name}")
            if c2.button(f"Add Back", key=f"oos_{i}_{item_name}"):
                 add_to_list({
                        "item": item_name,
                        "category": "General",
                        "quantity": 1, 
                        "unit": "pcs", 
                        "expiry_date": datetime.now() + timedelta(days=7)
                 })
                 if item_name in st.session_state.out_of_stock:
                    st.session_state.out_of_stock.remove(item_name)
                 st.rerun()
        st.markdown("---")

    # 2. History Rules
    st.markdown("**Restock Predictions:**")
    for record in st.session_state.history:
        item_name = record['item'].lower()
        
        if item_name in [x.lower() for x in st.session_state.out_of_stock]:
            continue

        if item_name in USAGE_RULES:
            days_since_buy = (datetime.now() - record['last_bought']).days
            expected_duration = USAGE_RULES[item_name]
            
            if days_since_buy > expected_duration:
                suggestions_found = True
                st.write(f"- **{record['item']}** (Last bought {days_since_buy} days ago)")
                if st.button(f"Add {record['item']}", key=f"pred_{item_name}"):
                    add_to_list({
                        "item": record['item'],
                        "category": "General",
                        "quantity": 1, 
                        "unit": "pcs", 
                        "expiry_date": datetime.now() + timedelta(days=7)
                    })
                    st.rerun()

    if not suggestions_found:
        st.caption("No restocking predictions needed right now.")

# --- RIGHT COLUMN: HEALTH CHECK ---
with col_dash_2:
    st.subheader("🥗 Health Check")
    
    health_tips_found = False
    inventory_items = [item['item'].lower() for item in st.session_state.inventory]
    
    for unhealthy, healthy in HEALTH_DB.items():
        if unhealthy in inventory_items:
            health_tips_found = True
            
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                c1.markdown(f"Found **{unhealthy.title()}**")
                c1.caption(f"Suggestion: {healthy.title()}")
                
                if c2.button(f"Add {healthy.title()}", key=f"rec_{unhealthy}"):
                      add_to_list({
                        "item": healthy.title(),
                        "category": "General",
                        "quantity": 1, 
                        "unit": "pcs", 
                        "expiry_date": datetime.now() + timedelta(days=7)
                      })
                      st.success(f"Added {healthy}!")
                      st.rerun()
    
    if not health_tips_found:
            st.success("Your pantry looks healthy! 🍎")

st.markdown("---")