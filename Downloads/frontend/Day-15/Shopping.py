import datetime
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Pro POS & Billing Suite (INR)",
    page_icon="💎",
    layout="wide",
)

# Custom CSS for styling
st.markdown("""
    <style>
    .receipt-box {
        background-color: #f8fafc;
        border: 1px dashed #cbd5e1;
        padding: 20px;
        border-radius: 10px;
        color: #0f172a;
    }
    .final-amount-banner {
        background-color: #0f172a;
        color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-size: 22px;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session States
if "cart" not in st.session_state:
  st.session_state.cart = []
if "invoice_history" not in st.session_state:
  st.session_state.invoice_history = []

if "catalog" not in st.session_state:
  st.session_state.catalog = [
      {"name": "Wireless Mouse", "price": 799.00, "category": "Electronics"},
      {"name": "Mechanical Keyboard", "price": 2499.00, "category": "Electronics"},
      {"name": "USB-C Hub", "price": 1299.00, "category": "Electronics"},
      {"name": "Executive Notebook", "price": 299.00, "category": "Stationery"},
      {"name": "Ceramic Coffee Mug", "price": 499.00, "category": "Kitchenware"},
  ]

# --- TOP DASHBOARD METRICS ---
st.title("💎 Enterprise POS & Billing Suite (INR)")
st.markdown("Streamline your store checkout experience with real-time calculations in Indian Rupees (Rs.), automated receipts, and business analytics.")
st.divider()

total_revenue = sum(float(inv["Total Amount"].replace("Rs. ", "").replace(",", "")) for inv in st.session_state.invoice_history)
total_orders = len(st.session_state.invoice_history)
current_cart_items = sum(item["quantity"] for item in st.session_state.cart)

m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="📊 Total Session Revenue", value=f"Rs. {total_revenue:,.2f}")
with m2:
    st.metric(label="🛍️ Completed Transactions", value=total_orders)
with m3:
    st.metric(label="🛒 Items in Active Cart", value=current_cart_items)

st.divider()

# Sidebar Setup
with st.sidebar:
  st.header("⚙️ POS Configurations")
  store_name = st.text_input("Store Name", value="Apex Global Retail India")
  store_address = st.text_area("Store Address", value="Cyber City, Phase 2, Gurgaon, Haryana")

  st.divider()
  st.header("👤 Customer & Payment")
  customer_name = st.text_input("Customer Name", value="Walk-in Guest")
  
  # --- STRICT 10-DIGIT MOBILE NUMBER VALIDATION ---
  customer_phone = st.text_input(
      "Mobile Number (10 digits only)", 
      value="", 
      max_chars=10, 
      placeholder="e.g. 9876543210"
  )
  
  # Validation check message if length is incorrect and not empty
  if customer_phone and (not customer_phone.isdigit() or len(customer_phone) != 10):
    st.error("⚠️ Mobile number must be exactly 10 digits.")

  payment_mode = st.selectbox(
      "Payment Method", ["UPI / QR 📱", "Cash 💵", "Credit Card 💳", "Debit Card 🏧"]
  )

  st.divider()
  st.header("🏷️ Tax & Discounts")
  discount_pct = st.slider("Discount (%)", 0.0, 50.0, 5.0, 1.0)
  tax_pct = st.slider("GST (%)", 0.0, 30.0, 18.0, 0.5)

  st.divider()
  if st.button("🗑️ Reset Cart", type="secondary", use_container_width=True):
    st.session_state.cart = []
    st.success("Cart cleared!")
    st.rerun()

# --- MAIN LAYOUT ---
col_catalog, col_manual, col_bill = st.columns([1.2, 1.2, 1.8], gap="medium")

with col_catalog:
  st.subheader("⚡ Quick Catalog")
  st.caption("Click to instantly add pre-loaded stock.")

  for idx, cat_item in enumerate(st.session_state.catalog):
    c_info, c_btn = st.columns([2, 1])
    with c_info:
      st.markdown(f"**{cat_item['name']}** \n`Rs. {cat_item['price']:,.2f}` *({cat_item['category']})*")
    with c_btn:
      if st.button("Add ➕", key=f"cat_{idx}", use_container_width=True):
        found = False
        for item in st.session_state.cart:
          if item["name"] == cat_item["name"]:
            item["quantity"] += 1
            item["total"] = item["quantity"] * item["price"]
            found = True
            break
        if not found:
          st.session_state.cart.append({
              "name": cat_item["name"],
              "price": cat_item["price"],
              "quantity": 1,
              "total": cat_item["price"],
          })
        st.rerun()
    st.markdown("---")

  with st.expander("➕ Add Item to Catalog"):
    with st.form("new_catalog_item"):
      nc_name = st.text_input("Item Name")
      nc_price = st.number_input("Price (Rs.)", min_value=1.00, format="%.2f")
      nc_cat = st.text_input("Category", value="General")
      submitted_nc = st.form_submit_button("Save to Inventory", use_container_width=True)
      if submitted_nc and nc_name:
        st.session_state.catalog.append(
            {"name": nc_name, "price": nc_price, "category": nc_cat}
        )
        st.success(f"Added {nc_name} to catalog!")
        st.rerun()

with col_manual:
  st.subheader("📦 Custom Product")
  with st.form("product_form", clear_on_submit=True):
    prod_name = st.text_input("Product Name")
    prod_price = st.number_input("Unit Price (Rs.)", min_value=1.00, format="%.2f", step=10.00)
    prod_qty = st.number_input("Quantity", min_value=1, max_value=1000, step=1)

    submitted = st.form_submit_button("➕ Add to Cart", use_container_width=True)
    if submitted:
      if prod_name.strip() == "":
        st.error("Please enter a valid product name.")
      else:
        item_exists = False
        for item in st.session_state.cart:
          if item["name"].lower() == prod_name.strip().lower():
            item["quantity"] += prod_qty
            item["total"] = item["quantity"] * item["price"]
            item_exists = True
            break

        if not item_exists:
          st.session_state.cart.append({
              "name": prod_name.strip(),
              "price": prod_price,
              "quantity": prod_qty,
              "total": prod_price * prod_qty,
          })
        st.success(f"Added {prod_qty}x {prod_name}!")
        st.rerun()

  if st.session_state.cart:
    st.markdown("### 🛒 Active Cart Management")
    for index, item in enumerate(st.session_state.cart):
      col_item, col_del = st.columns([3, 1])
      with col_item:
        st.text(f"{item['name']} (x{item['quantity']})")
      with col_del:
        if st.button("❌", key=f"del_{index}"):
          st.session_state.cart.pop(index)
          st.rerun()

with col_bill:
  st.subheader("📄 Live Thermal Invoice")

  if not st.session_state.cart:
    st.info("Your cart is empty. Add products to render the real-time invoice preview.")
  else:
    # Calculations
    subtotal = sum(item["total"] for item in st.session_state.cart)
    calculated_discount = subtotal * (discount_pct / 100.0)
    taxable_amount = subtotal - calculated_discount
    calculated_tax = taxable_amount * (tax_pct / 100.0)
    final_amount = taxable_amount + calculated_tax

    # Receipt Header Container
    with st.container():
      phone_display = f"({customer_phone})" if customer_phone else ""
      st.markdown(f"""
      <div class="receipt-box">
          <h2 style='text-align: center; color: #1e293b; margin-bottom: 0;'>{store_name}</h2>
          <p style='text-align: center; color: #64748b; font-size: 13px;'>{store_address}</p>
          <hr style='border: 0.5px solid #cbd5e1;'>
          <p style='margin: 2px 0;'><b>Customer:</b> {customer_name} {phone_display}</p>
          <p style='margin: 2px 0;'><b>Payment Method:</b> {payment_mode}</p>
          <p style='margin: 2px 0;'><b>Timestamp:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
          <hr style='border: 0.5px solid #cbd5e1;'>
      """, unsafe_allow_html=True)

      # Table format for items
      display_data = []
      for item in st.session_state.cart:
        display_data.append({
            "Item": item["name"],
            "Qty": item["quantity"],
            "Price": f"Rs. {item['price']:,.2f}",
            "Total": f"Rs. {item['total']:,.2f}",
        })
      st.table(display_data)

      # Subtotals & Tax Breakdown
      st.markdown(f"""
          <div style='text-align: right; font-size: 15px;'>
              <b>Subtotal:</b> Rs. {subtotal:,.2f}<br>
              {f"<b>Discount ({discount_pct}%):</b> -Rs. {calculated_discount:,.2f}<br>" if discount_pct > 0 else ""}
              {f"<b>GST ({tax_pct}%):</b> +Rs. {calculated_tax:,.2f}<br>" if tax_pct > 0 else ""}
          </div>
      """, unsafe_allow_html=True)

      # CLEAN FINAL PAYABLE AMOUNT BANNER
      st.markdown(f"""
          <div class="final-amount-banner">
              Total Payable Amount: Rs. {final_amount:,.2f}
          </div>
      """, unsafe_allow_html=True)

      st.markdown("""
          <hr style='border: 0.5px solid #cbd5e1;'>
          <p style='text-align: center; color: #64748b; font-size: 12px;'>Thank you for your business! Dhanyawad.</p>
      </div>
      """, unsafe_allow_html=True)

    # Optional Cash Tendered Input
    if "Cash" in payment_mode:
      cash_given = st.number_input("💵 Cash Given by Customer (Rs.)", min_value=0.0, value=float(final_amount), step=50.0)
      if cash_given >= final_amount:
        change_due = cash_given - final_amount
        st.success(f"**Change to Return:** Rs. {change_due:,.2f}")
      else:
        st.warning(f"⚠️ Insufficient cash! Short by Rs. {final_amount - cash_given:,.2f}")

    # Action Buttons
    b1, b2 = st.columns(2)
    with b1:
      bill_text = f"""=====================================
          {store_name.upper()}
       {store_address}
=====================================
Customer: {customer_name} {phone_display}
Payment: {payment_mode}
Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-------------------------------------
"""
      for item in st.session_state.cart:
        bill_text += f"{item['name']} x {item['quantity']} @ Rs. {item['price']:,.2f} = Rs. {item['total']:,.2f}\n"
      bill_text += f"""-------------------------------------
Subtotal: Rs. {subtotal:,.2f}
Discount ({discount_pct}%): -Rs. {calculated_discount:,.2f}
GST ({tax_pct}%): +Rs. {calculated_tax:,.2f}
-------------------------------------
FINAL PAYABLE AMOUNT: Rs. {final_amount:,.2f}
=====================================
     Thank you for your business!
"""
      st.download_button(
          label="📥 Download Receipt",
          data=bill_text,
          file_name=f"receipt_{customer_name.replace(' ', '_')}.txt",
          mime="text/plain",
          use_container_width=True,
      )

    with b2:
      # Block checkout if phone number is entered incorrectly (must be blank or exactly 10 digits)
      is_phone_valid = (not customer_phone) or (customer_phone.isdigit() and len(customer_phone) == 10)
      
      if st.button("💾 Checkout & Log Order", type="primary", use_container_width=True):
        if not is_phone_valid:
          st.error("❌ Cannot checkout! Please ensure the mobile number is exactly 10 digits.")
        else:
          invoice_record = {
              "Customer": f"{customer_name} ({customer_phone})" if customer_phone else customer_name,
              "Mode": payment_mode,
              "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
              "Items Count": len(st.session_state.cart),
              "Total Amount": f"Rs. {final_amount:,.2f}",
          }
          st.session_state.invoice_history.append(invoice_record)
          st.success("Checkout successful! Order logged.")
          st.session_state.cart = []
          st.rerun()

# --- COMPLETED ORDERS LOG SECTION ---
if st.session_state.invoice_history:
  st.divider()
  st.subheader("📊 Completed Transaction Archive")
  search_query = st.text_input("🔍 Search past orders by customer name...")
  
  filtered_history = st.session_state.invoice_history
  if search_query:
    filtered_history = [
        inv for inv in st.session_state.invoice_history
        if search_query.lower() in inv["Customer"].lower()
    ]
  st.table(filtered_history)