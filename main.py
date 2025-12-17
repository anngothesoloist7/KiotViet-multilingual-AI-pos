import os
import uuid
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI

# 1. Initialize the App
app = Flask(__name__)
CORS(app)

# === IN-MEMORY DATABASE (The Menu System) ===
# Allows the frontend to save items and look up prices automatically.
MENU_DB = [
    # === BURGERS & SANDWICHES ===
    {"id": "1", "name": "Classic Beef Burger", "price": 65000},
    {"id": "2", "name": "Double Cheese Burger", "price": 85000},
    {"id": "3", "name": "Spicy Chicken Burger", "price": 60000},
    {"id": "4", "name": "Fish Fillet Sandwich", "price": 55000},

    # === RICE & NOODLES (ASIAN CORNER) ===
    {"id": "5", "name": "Hainanese Chicken Rice", "price": 50000},
    {"id": "6", "name": "Beef Noodle Soup", "price": 55000}, # Phở
    {"id": "7", "name": "Grilled Pork Vermicelli", "price": 60000}, # Bún chả
    {"id": "8", "name": "Vegetarian Fried Rice", "price": 45000},

    # === SIDES & SNACKS ===
    {"id": "9", "name": "French Fries", "price": 25000},
    {"id": "10", "name": "Onion Rings", "price": 30000},
    {"id": "11", "name": "Chicken Nuggets (6pcs)", "price": 40000},
    {"id": "12", "name": "Coleslaw", "price": 15000},

    # === DRINKS ===
    {"id": "13", "name": "Coke", "price": 15000},
    {"id": "14", "name": "Diet Coke", "price": 15000},
    {"id": "15", "name": "Sprite", "price": 15000},
    {"id": "16", "name": "Iced Coffee", "price": 25000},
    {"id": "17", "name": "Peach Tea", "price": 30000},
    {"id": "18", "name": "Mineral Water", "price": 10000},

    # === DESSERTS ===
    {"id": "19", "name": "Vanilla Ice Cream", "price": 15000},
    {"id": "20", "name": "Chocolate Sundae", "price": 25000},
    {"id": "21", "name": "Apple Pie", "price": 20000}
]

# === ROUTE 1: THE HOMEPAGE ===
@app.route('/')
def index():
    return send_file('index.html')

# === ROUTE 2: MENU API ===
@app.route('/menu', methods=['GET'])
def get_menu():
    """Returns the full list of menu items."""
    return jsonify({"items": MENU_DB})

@app.route('/menu', methods=['POST'])
def add_menu_item():
    """Adds a new item to the menu via HTTP (Manual Entry)."""
    data = request.json
    if not data or 'name' not in data or 'price' not in data:
        return jsonify({"error": "Invalid data"}), 400

    new_item = {
        "id": str(uuid.uuid4()),
        "name": data['name'],
        "price": int(data['price'])
    }
    MENU_DB.append(new_item)
    return jsonify(new_item)

@app.route('/menu/<item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    """Deletes an item from the menu."""
    global MENU_DB
    MENU_DB = [item for item in MENU_DB if item['id'] != item_id]
    return jsonify({"success": True})

# 2. Connect to OpenAI
client = OpenAI(api_key="abcdef")

# 3. The Logic (The "Brain")
simplified_menu = [
    {"n": item["name"], "p": item["price"]} for item in MENU_DB
]
current_menu_items_str = json.dumps(simplified_menu, ensure_ascii=False)
SYSTEM_PROMPT = f"""
    You are an AI Cashier. 
    
    ### CONTEXT - MENU DATA:
    {current_menu_items_str}

    ### OUTPUT JSON SCHEMA:
    {{
      "intent": "TRANSACTION" | "SYSTEM" | null, 
      "global_command": "CLEAR_CART" | "CHECKOUT" | "SHOW_CART" | null,
      "results": [
        {{
          "action": "add" | "remove", 
          "item": "string (Title Case)",
          "quantity": integer,
          "price": number or null, 
          "modifiers": ["string"]
        }}
      ]
    }}

    ### LOGIC PRIORITY (MUST FOLLOW ORDER):

    1. **PRIORITY 0: SYSTEM COMMANDS** (Top Priority)
       - Triggers: "Clear cart", "Empty cart", "Delete all", "Start over", "Checkout", "Pay", "Bill please".
       - Action: Set "intent": "SYSTEM" and fill "global_command".
       - Rule: If a system command is detected, "results" MUST be empty [].

    2. **PRIORITY 1: TRANSACTION & MIXED COMMANDS**
       - Triggers: Ordering food, removing items, changing items.
       - Action: Set "intent": "TRANSACTION".
       
       **CRITICAL RULES FOR MIXED COMMANDS:**
       A. **SEGMENTATION**: Break sentence by "and", "then", "but", "instead". Process segments independently.
       B. **VERB BINDING**:
          - Words: "Remove", "Drop", "Cancel", "No", "Less" -> Set "action": "remove".
          - Words: "Add", "Get", "Want", "More", "One" -> Set "action": "add".
       C. **"CHANGE" LOGIC**:
          - Phrase: "Change [Item A] to [Item B]"
          - Logic: Create TWO entries -> 1. Remove [Item A], 2. Add [Item B].

    ### FEW-SHOT EXAMPLES:

    **User:** "Clear the cart please."
    **JSON:** {{ "intent": "SYSTEM", "global_command": "CLEAR_CART", "results": [] }}

    **User:** "I want to checkout."
    **JSON:** {{ "intent": "SYSTEM", "global_command": "CHECKOUT", "results": [] }}

    **User:** "Remove the ice cream and add a coffee."
    **JSON:** {{
      "intent": "TRANSACTION",
      "global_command": null,
      "results": [
         {{ "action": "remove", "item": "Vanilla Ice Cream", "quantity": 1, "price": null, "modifiers": [] }},
         {{ "action": "add", "item": "Iced Coffee", "quantity": 1, "price": null, "modifiers": [] }}
      ]
    }}

    **User:** "Actually change the Burger to a Pizza."
    **JSON:** {{
      "intent": "TRANSACTION",
      "global_command": null,
      "results": [
         {{ "action": "remove", "item": "Burger", "quantity": 1, "price": null, "modifiers": [] }},
         {{ "action": "add", "item": "Pizza", "quantity": 1, "price": null, "modifiers": [] }}
      ]
    }}
    """

@app.route('/process_audio', methods=['POST'])
def process_audio():
    # Validation
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['file']
    unique_filename = f"temp_{uuid.uuid4()}.mp3"
    audio_file.save(unique_filename)

    try:
        audio_file_read = open(unique_filename, "rb")

        # === API 1: AUDIO TRANSCRIBING ===
        print("Calling Api1 (Whisper)...")

        # Inject current menu names into context for better recognition
        menu_names = ", ".join([item['name'] for item in MENU_DB])
        MY_CONTEXT = (
            f"Transcript of a customer ordering food in English. "
            f"The menu includes: {menu_names}. "
            f"Common phrases: I want to add, remove, change to, no chili, less sugar, takeaway. "
            f"Commands: Checkout, Cart, Confirm."
        )

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file_read,
            language="en",
            prompt=MY_CONTEXT, 
            temperature=0.0
        )
        user_text = transcript.text
        print(f"User said: {user_text}")

        # === API 2: JSON CONVERSION ===
        print("Calling Api2 (GPT Parser)...")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            response_format={ "type": "json_object" },
            temperature=0
        )

        json_response_str = completion.choices[0].message.content
        print(f"AI Response: {json_response_str}") 

        data = json.loads(json_response_str)
        
        intent = data.get("intent")
        global_command = data.get("global_command")
        results = data.get("results", [])

        # === 1. XỬ LÝ LỆNH HỆ THỐNG (Clear/Checkout) ===
        if global_command == "CLEAR_CART":
            print(">>> COMMAND: CLEAR CART")
            # TODO: Add logic to clear cart variable here
        elif global_command == "CHECKOUT":
            print(">>> COMMAND: CHECKOUT")

        # === 2. XỬ LÝ ADMIN (Thêm vào Menu DB) ===
        elif intent == "ADD_TO_MENU":
            # (Logic cũ giữ nguyên)
            pass

        # === 3. XỬ LÝ GIAO DỊCH (Thêm/Bớt món) ===
        elif intent == "TRANSACTION":
            for order_item in results:
                # [LOGIC MỚI]
                # 1. Lấy giá trị action từ JSON
                raw_action = order_item.get("action")
                
                # 2. Kiểm tra: Nếu không có (None) hoặc rỗng ("") -> Gán mặc định "add"
                # Ngược lại -> Chuẩn hóa về chữ thường (để xử lý "Remove", "REMOVE" thành "remove")
                if not raw_action:
                    action = "add"
                else:
                    action = str(raw_action).lower().strip()

                item_name = order_item.get("item")
                quantity = order_item.get("quantity", 1)
                
                # Logic điền giá (Price injection) - GIỮ NGUYÊN
                if order_item.get("price") is None:
                     found = next((m for m in MENU_DB if m["name"].lower() == item_name.lower()), None)
                     if found: 
                         order_item["price"] = found["price"]

                # IN RA LOG
                if action == "add":
                     print(f" (+) ADDING: {quantity} x {item_name}")
                elif action == "remove":
                     print(f" (-) REMOVING: {quantity} x {item_name}")
                else:
                     # Phòng trường hợp AI trả về từ lạ như "update", "change"
                     print(f" [!] UNKNOWN ACTION ({action}): {quantity} x {item_name} -> Defaulting to ADD")
                     # Nếu muốn an toàn tuyệt đối, có thể ép nó thực hiện add ở đây luôn

        # 1. Đóng file và xóa file tạm
        audio_file_read.close()
        if os.path.exists(unique_filename):
            os.remove(unique_filename)

        # 2. Trả về kết quả JSON cho Frontend
        return jsonify(data)
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(unique_filename):
            os.remove(unique_filename)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)