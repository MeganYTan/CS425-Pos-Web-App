from flask import Blueprint, request, jsonify
from mysql.connector import Error as MySQL_Error

from db import mydb
import logging

logger = logging.getLogger(__name__)
customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/', methods=['GET'])
def get_all_customers():
    connection = mydb()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM CUSTOMER")
    result = cursor.fetchall()
    return jsonify(result), 200
@customer_bp.route('/<int:id>', methods=['GET'])
def get_customer_by_id(id):
    connection = mydb()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (id,))
        customer = cursor.fetchone()
        if not customer:
            return jsonify({'message': 'Customer not found!'}), 404
    finally:
        cursor.close()
        connection.close()
    return jsonify(customer), 200



@customer_bp.route('/add', methods=['POST'])
def add():
    data = request.json
    logger.debug(data)
    connection = mydb()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `customer` (`name_first_name`, `name_last_name`, `email`, `loyalty_points`, `phone_number`) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (data['name_first_name'], data['name_last_name'], data['email'], data['loyalty_points'], data['phone_number']))
            customer_id = cursor.lastrowid
        connection.commit()
    except MySQL_Error as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        return jsonify({'message': 'Error Adding Customer', 'success': False}), 500
    finally:
        connection.close()

    return jsonify({'message': 'Customer added successfully!', 'customer_id': customer_id}), 201

@customer_bp.route('/edit/<int:customer_id>', methods=['POST'])
def edit(customer_id):
    data = request.json
    connection = mydb()
    cursor = connection.cursor(prepared=True)
    try:
        sql = "UPDATE CUSTOMER SET name_first_name = %s, name_last_name=%s, email=%s, loyalty_points=%s, phone_number=%s WHERE customer_id=%s"
        cursor.execute(sql, (data['name_first_name'], data['name_last_name'], data['email'], data['loyalty_points'], data['phone_number'], customer_id))
        logger.debug(cursor._executed)
        # if cursor.rowcount == 0:
        #     return jsonify({'message': 'Customer not found!'}), 404
        connection.commit()
    except MySQL_Error as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        return jsonify({'message': 'Error Updating Customer', 'success': False}), 500
    finally:
        connection.close()

    return jsonify({'message': 'Customer updated successfully!', 'success': True}), 200

@customer_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    connection = mydb()
    cursor = connection.cursor(prepared=True)
    try:
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (id,))
        if cursor.rowcount == 0:
            return jsonify({'message': 'Customer not found!'}), 404
        connection.commit()
    except MySQL_Error as e:
        connection.rollback()
        logger.error(f"MySQL Error: {e}")
        return jsonify({'message': 'Error Deleting Customer', 'success': False}), 500
    finally:
        # cursor.close()
        connection.close()

    return jsonify({'message': 'Customer deleted successfully!'}), 200