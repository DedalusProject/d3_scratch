
import pytest
import numpy as np
from dedalus.core import coords, distributor, basis, field, operators, problems, solvers, arithmetic
from dedalus.core import future
from dedalus.tools.array import apply_matrix
from dedalus.tools.cache import CachedFunction


dot = arithmetic.DotProduct
Nphi_range = [8]
Ntheta_range = [8]
Nr_range = [12]
radius_ball = 1.5
radii_shell = (0.5, 1)
dealias = [3/2]
dtypes = [np.float64, np.complex128]

@CachedFunction
def build_ball(Nphi, Ntheta, Nr, dealias, dtype):
    c = coords.SphericalCoordinates('phi', 'theta', 'r')
    d = distributor.Distributor((c,))
    b = basis.BallBasis(c, (Nphi, Ntheta, Nr), radius=radius_ball, dealias=(dealias, dealias, dealias), dtype=dtype)
    phi, theta, r = b.local_grids()
    x, y, z = c.cartesian(phi, theta, r)
    return c, d, b, phi, theta, r, x, y, z

@CachedFunction
def build_shell(Nphi, Ntheta, Nr, dealias, dtype):
    c = coords.SphericalCoordinates('phi', 'theta', 'r')
    d = distributor.Distributor((c,))
    b = basis.SphericalShellBasis(c, (Nphi, Ntheta, Nr), radii=radii_shell, dealias=(dealias, dealias, dealias), dtype=dtype)
    phi, theta, r = b.local_grids()
    x, y, z = c.cartesian(phi, theta, r)
    return c, d, b, phi, theta, r, x, y, z


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_scalar_prod_scalar(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)
    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)
    f['g'] = r**4
    g['g'] = (3*x**2 + 2*y*z)
    vars = [g]
    if ncc_first:
        w0 = f * g
    else:
        w0 = g * f
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)
    problem = problems.LBVP(vars)
    problem.add_equation((w1, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)
    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_scalar_prod_vector(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)

    f['g'] = r**6
    g['g'] = 3*x**2 + 2*y*z
    u = operators.Gradient(g, c).evaluate()

    vars = [u]
    if ncc_first:
        w0 = f * u
    else:
        w0 = u * f
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((w1, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)

    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_scalar_prod_tensor(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)

    f['g'] = r**6
    g['g'] = 3*x**2 + 2*y*z
    T = operators.Gradient(operators.Gradient(g, c), c).evaluate()

    vars = [T]
    if ncc_first:
        w0 = f * T
    else:
        w0 = T * f
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((w1, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)

    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_vector_prod_scalar(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)


    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)

    f['g'] = r**6
    g['g'] = 3*x**2 + 2*y*z
    u = operators.Gradient(f, c).evaluate()

    vars = [g]
    if ncc_first:
        w0 = u * g
    else:
        w0 = g * u
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((dot(u,u)*g, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)

    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_vector_prod_vector(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)

    f['g'] = r**6
    g['g'] = 3*x**2 + 2*y*z
    u = operators.Gradient(f, c).evaluate()
    v = operators.Gradient(g, c).evaluate()

    vars = [v]
    if ncc_first:
        w0 = u * v
    else:
        w0 = v * u
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((dot(u,u)*v, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)

    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_vector_dot_vector(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)

    f['g'] = r**6
    g['g'] = 3*x**2 + 2*y*z
    u = operators.Gradient(f, c).evaluate()
    v = operators.Gradient(g, c).evaluate()

    vars = [v]
    if ncc_first:
        w0 = dot(u, v)
    else:
        w0 = dot(v, u)
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((dot(u,u)*v, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)

    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_vector_dot_tensor(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    T = field.Field(dist=d, bases=(b,), tensorsig=(c,c,), dtype=dtype)

    T['g'][2,2] = (6*x**2+4*y*z)/r**2
    T['g'][2,1] = T['g'][1,2] = -2*(y**3+x**2*(y-3*z)-y*z**2)/(r**3*np.sin(theta))
    T['g'][2,0] = T['g'][0,2] = 2*x*(z-3*y)/(r**2*np.sin(theta))
    T['g'][1,1] = 6*x**2/(r**2*np.sin(theta)**2) - (6*x**2+4*y*z)/r**2
    T['g'][1,0] = T['g'][0,1] = -2*x*(x**2+y**2+3*y*z)/(r**3*np.sin(theta)**2)
    T['g'][0,0] = 6*y**2/(x**2+y**2)

    f['g'] = r**6
    u = operators.Gradient(f, c).evaluate()

    vars = [T]
    if ncc_first:
        w0 = dot(u, T)
    else:
        w0 = dot(T, u)
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((dot(u,u)*T, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)

    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_tensor_prod_scalar(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)

    f['g'] = r**6
    g['g'] = 3*x**2 + 2*y*z
    T = operators.Gradient(operators.Gradient(f, c), c).evaluate()

    vars = [g]
    if ncc_first:
        U0 = T * g
    else:
        U0 = g * T
    U1 = U0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((f*g, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    U1.store_ncc_matrices(vars, solver.subproblems)

    U0 = U0.evaluate()
    U0.require_scales(1)
    U1 = U1.evaluate_as_ncc()
    assert np.allclose(U0['g'], U1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_tensor_dot_vector(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    g = field.Field(dist=d, bases=(b,), dtype=dtype)

    f['g'] = r**6
    g['g'] = 3*x**2 + 2*y*z
    T = operators.Gradient(operators.Gradient(f, c), c).evaluate()
    u = operators.Gradient(g, c).evaluate()

    vars = [u]
    if ncc_first:
        w0 = dot(T, u)
    else:
        w0 = dot(u, T)
    w1 = w0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((f*u, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    w1.store_ncc_matrices(vars, solver.subproblems)

    w0 = w0.evaluate()
    w0.require_scales(1)
    w1 = w1.evaluate_as_ncc()
    assert np.allclose(w0['g'], w1['g'])


@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('Nr', Nr_range)
@pytest.mark.parametrize('basis', [build_ball, build_shell])
@pytest.mark.parametrize('ncc_first', [True,False])
@pytest.mark.parametrize('dealias', dealias)
@pytest.mark.parametrize('dtype', dtypes)
def test_tensor_dot_tensor(Nphi, Ntheta, Nr, basis, ncc_first, dealias, dtype):
    c, d, b, phi, theta, r, x, y, z = basis(Nphi, Ntheta, Nr, dealias=dealias, dtype=dtype)

    f = field.Field(dist=d, bases=(b.radial_basis,), dtype=dtype)
    f['g'] = r**6
    U = operators.Gradient(operators.Gradient(f, c), c).evaluate()

    T = field.Field(dist=d, bases=(b,), tensorsig=(c,c,), dtype=dtype)

    T['g'][2,2] = (6*x**2+4*y*z)/r**2
    T['g'][2,1] = T['g'][1,2] = -2*(y**3+x**2*(y-3*z)-y*z**2)/(r**3*np.sin(theta))
    T['g'][2,0] = T['g'][0,2] = 2*x*(z-3*y)/(r**2*np.sin(theta))
    T['g'][1,1] = 6*x**2/(r**2*np.sin(theta)**2) - (6*x**2+4*y*z)/r**2
    T['g'][1,0] = T['g'][0,1] = -2*x*(x**2+y**2+3*y*z)/(r**3*np.sin(theta)**2)
    T['g'][0,0] = 6*y**2/(x**2+y**2)

    vars = [T]
    if ncc_first:
        W0 = dot(T, U)
    else:
        W0 = dot(U, T)
    W1 = W0.reinitialize(ncc=True, ncc_vars=vars)

    problem = problems.LBVP(vars)
    problem.add_equation((f*T, 0))
    solver = solvers.LinearBoundaryValueSolver(problem, matsolver='SuperluNaturalSpsolve')
    W1.store_ncc_matrices(vars, solver.subproblems)

    W0 = W0.evaluate()
    W0.require_scales(1)
    W1 = W1.evaluate_as_ncc()
    assert np.allclose(W0['g'], W1['g'])
