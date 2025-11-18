from flask import render_template, request
from modules.employees import employees_bp
from modules.auth.routes import login_required
from models import Employee, Department

@employees_bp.route('/')
@login_required
def index():
    """Lista de empleados (directorio)"""
    search = request.args.get('search', '')

    if search:
        employees = Employee.search(search)
    else:
        employees = Employee.get_all()

    departments = Department.get_all()

    return render_template('employees/index.html',
                         employees=employees,
                         departments=departments,
                         search=search)

@employees_bp.route('/<int:employee_id>')
@login_required
def detail(employee_id):
    """Detalle de un empleado"""
    employee = Employee.get_by_id(employee_id)

    if not employee:
        return "Empleado no encontrado", 404

    return render_template('employees/detail.html', employee=employee)
