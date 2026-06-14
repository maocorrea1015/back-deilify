import click
from flask.cli import with_appcontext
from datetime import datetime
from sqlalchemy import update, select
from ..extensions import db_session
from ..models.factura import Factura, EstadoFactura

@click.group()
def cartera_cli():
    """Comandos para el módulo de cartera"""
    pass

@cartera_cli.command('check-overdue')
@with_appcontext
def check_overdue():
    """Marca como VENCIDAS las facturas que pasaron su fecha de vencimiento"""
    ahora = datetime.utcnow()
    
    stmt = (
        update(Factura)
        .where(
            Factura.fecha_vencimiento < ahora,
            Factura.saldo_pendiente > 0,
            Factura.estado == EstadoFactura.PENDIENTE
        )
        .values(estado=EstadoFactura.VENCIDA)
    )
    
    result = db_session.execute(stmt)
    db_session.commit()
    
    click.echo(f"Proceso completado. Facturas actualizadas: {result.rowcount}")
