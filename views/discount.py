from flask import Blueprint, request, jsonify
from mysql.connector import Error as MySQL_Error
from .helper import get_serializable_data, get_serializable_item
from config import mydb
import logging

logger = logging.getLogger(__name__)
discount_bp = Blueprint('discount', __name__)


# get all discounts
@discount_bp.route('/', methods=['GET'])
def get_all_discounts():
    connection = mydb()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM DISCOUNT")
    result = cursor.fetchall()
    result = get_serializable_data(result)
    return jsonify(result), 200


# get discount by id. Parameter: id: id of the discount to get
@discount_bp.route('/<int:id>', methods=['GET'])
def get_discount_by_id(id):
    connection = mydb()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM discount WHERE discount_id = %s", (id,))
        discount = cursor.fetchone()
        discount = get_serializable_item(discount)
        if not discount:
            return jsonify({'message': 'Discount not found!'}), 404
    finally:
        cursor.close()
        connection.close()
    return jsonify(discount), 200

#new query for olap
@discount_bp.route('/sales-report', methods=['GET'])
def get_discount_sales_report():
    connection = mydb()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                DISCOUNT.discount_description, 
                COUNT(*) as number_of_orders, 
                SUM(PRODUCT.price * ORDER_PRODUCT.quantity) as total_sales_without_discount, 
                SUM((PRODUCT.price * ORDER_PRODUCT.quantity) * (1 - DISCOUNT.discount_amount/100)) as total_sales_with_discount
            FROM ORDERS
            JOIN ORDER_PRODUCT ON ORDERS.order_id = ORDER_PRODUCT.order_id
            JOIN PRODUCT ON ORDER_PRODUCT.product_id = PRODUCT.product_id
            LEFT JOIN DISCOUNT ON ORDERS.discount_id = DISCOUNT.discount_id
            GROUP BY DISCOUNT.discount_description;
        """)
        result = cursor.fetchall()
        result = get_serializable_data(result)
        return jsonify(result), 200
    except MySQL_Error as e:
        logger.error(f"MySQL Error: {e}")
        return jsonify({'message': 'Error retrieving sales report: ' + str(e), 'success': False}), 500
    finally:
        cursor.close()
        connection.close()

# add a discount to the database. Parameter in post body is the discount object
@discount_bp.route('/add', methods=['POST'])
def add():
    data = request.json
    connection = mydb()
    try:
        with connection.cursor() as cursor:
            sql = ("INSERT INTO `discount` (`discount_description`, `discount_amount`, `coupon_code`) VALUES (%s, %s, "
                   "%s)")
            cursor.execute(sql, (data['discount_description'], data['discount_amount'], data['coupon_code']))
            discount_id = cursor.lastrowid
        connection.commit()
    except MySQL_Error as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        return jsonify({'message': 'Error Adding Discount: ' + str(e), 'success': False}), 500
    finally:
        cursor.close()
        connection.close()
    return jsonify({'message': 'Discount added successfully!', 'discount_id': discount_id, 'success': True}), 201


# edit discount. Parameter: discount_id: the id of the discount to edit. The discount details are in the body of
# the post request
@discount_bp.route('/edit/<int:discount_id>', methods=['POST'])
def edit(discount_id):
    data = request.json
    connection = mydb()
    cursor = connection.cursor(prepared=True)
    try:
        sql = "UPDATE DISCOUNT SET discount_amount = %s, discount_description=%s, coupon_code=%s WHERE discount_id =%s"
        cursor.execute(sql, (data['discount_amount'], data['discount_description'], data['coupon_code'], discount_id))
        connection.commit()
    except MySQL_Error as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        return jsonify({'message': 'Error Updating Discount: ' + str(e), 'success': False}), 500
    finally:
        cursor.close()
        connection.close()
    return jsonify({'message': 'Discount updated successfully!', 'success': True}), 200


# delete discount. Parameter: id: the id of the discount to delete
@discount_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    connection = mydb()
    cursor = connection.cursor(prepared=True)
    try:
        cursor.execute("DELETE FROM discount WHERE discount_id = %s", (id,))
        if cursor.rowcount == 0:
            return jsonify({'message': 'Discount not found!'}), 404
        connection.commit()
    except MySQL_Error as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        return jsonify({'message': 'Error Deleting Discount:' + str(e), 'success': False}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': 'Discount deleted successfully!', 'success': True}), 200
