"""2-Sphere tests gradient, divergence, curl, laplacian."""

import pytest
import numpy as np
from dedalus.core import coords, distributor, basis, field, operators, arithmetic, problems, solvers
from dedalus.tools.cache import CachedFunction
from scipy.special import sph_harm

Nphi_range = [32]
Ntheta_range = [16]
dealias_range = [1, 3/2]
pi = np.pi

@CachedFunction
def build_sphere(Nphi, Ntheta, dealias, dtype):
    c = coords.S2Coordinates('phi', 'theta')
    d = distributor.Distributor((c,))
    b = basis.SWSH(c, (Nphi, Ntheta), radius=1, dealias=(dealias, dealias), dtype=dtype)
    phi, theta = b.local_grids(b.domain.dealias)
    #x, y = c.cartesian(phi, theta)
    return c, d, b, phi, theta#, x, y

@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('dtype', [np.complex128])
def test_implicit_divergence_cleaning(Nphi, Ntheta, dealias, dtype):
    """cleans divergence from a given vector field. Tests Div, Skew, and Grad.
    """
    c, d, b, phi, theta = build_sphere(Nphi, Ntheta, dealias, dtype)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    psi = field.Field(dist=d, bases=(b,), dtype=dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    h = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)

    f.set_scales(b.domain.dealias)
    u.set_scales(b.domain.dealias)
    h.set_scales(b.domain.dealias)
    psi.set_scales(b.domain.dealias)
    
    x = np.sin(theta)*np.cos(phi)
    y = np.sin(theta)*np.sin(phi)
    z = np.cos(theta)
    f['g'] = z**2

    grad = lambda A: operators.Gradient(A,c)
    div = lambda A: operators.Divergence(A)
    lap = lambda A: operators.Laplacian(A,c)
    skew = lambda A: basis.S2Skew(A)

    g = operators.Gradient(f, c).evaluate()
    hh = skew(g).evaluate()
    h['g'][0] = g['g'][1]
    h['g'][1] = -g['g'][0]
    assert np.allclose(hh['g'],h['g'])

    problem = problems.LBVP([u,psi])
    problem.add_equation((grad(psi) + u, h+g))
    problem.add_equation((div(u),0), condition='ntheta !=0')
    problem.add_equation((psi,0), condition='ntheta == 0')
    solver = solvers.LinearBoundaryValueSolver(problem)
    solver.solve()
    ug = [0*phi, 0*phi]
    assert np.allclose(u['g'], h['g'])

@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('dtype', [np.complex128])
def test_gradient_scalar(Nphi, Ntheta, dealias, dtype):
        #c, d, b, phi, theta, x, y = build_sphere(Nphi, Ntheta, dealias, dtype)
    c, d, b, phi, theta = build_sphere(Nphi, Ntheta, dealias, dtype)
    u = field.Field(dist=d, bases=(b,), dtype=dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    u.set_scales(b.domain.dealias)
    m = 2
    l = 2
    f['g'] = sph_harm(m,l,phi,theta)

    u = operators.Gradient(f,c).evaluate()

    ug = [1j*np.exp(2j*phi)*np.sqrt(15/(2*np.pi))*np.sin(theta)/2,
          np.exp(2j*phi)*np.sqrt(15/(2*np.pi))*np.cos(theta)*np.sin(theta)/2]
    assert np.allclose(u['g'], ug)

# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_gradient_radial_scalar(Ntheta, dealias, basis, dtype):
#     Nphi = 1
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype)
#     f = field.Field(dist=d, bases=(b,), dtype=dtype)
#     f.set_scales(b.domain.dealias)
#     f['g'] = r**4
#     u = operators.Gradient(f, c).evaluate()
#     ug = [0*r*phi, 4*r**3 + 0*phi]
#     assert np.allclose(u['g'], ug)


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_gradient_vector(Nphi, Ntheta, dealias, basis, dtype):
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype)
#     f = field.Field(dist=d, bases=(b,), dtype=dtype)
#     f.set_scales(b.domain.dealias)
#     f['g'] = 3*x**4 + 2*y*x
#     grad = lambda A: operators.Gradient(A, c)
#     T = grad(grad(f)).evaluate()
#     ex = np.array([-np.sin(phi)+0.*r,np.cos(phi)+0.*r])
#     ey = np.array([np.cos(phi)+0.*r,np.sin(phi)+0.*r])
#     exex = ex[:,None, ...] * ex[None,...]
#     eyex = ey[:,None, ...] * ex[None,...]
#     exey = ex[:,None, ...] * ey[None,...]
#     eyey = ey[:,None, ...] * ey[None,...]
#     Tg = 36*x**2*exex + 2*(exey + eyex)
#     assert np.allclose(T['g'], Tg)


# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_gradient_radial_vector(Ntheta, dealias, basis, dtype):
#     Nphi = 1
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype)
#     f = field.Field(dist=d, bases=(b,), dtype=dtype)
#     f.set_scales(b.domain.dealias)
#     f['g'] = r**4
#     grad = lambda A: operators.Gradient(A, c)
#     T = grad(grad(f)).evaluate()
#     er = np.array([[[0]], [[1]]])
#     ephi = np.array([[[1]], [[0]]])
#     erer = er[:, None, ...] * er[None, ...]
#     ephiephi = ephi[:, None, ...] * ephi[None, ...]
#     Tg = 12 * r**2 * erer + 4 * r**2 * ephiephi
#     assert np.allclose(T['g'], Tg)


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_divergence_vector(Nphi, Ntheta, dealias, basis, dtype):
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype)
#     f = field.Field(dist=d, bases=(b,), dtype=dtype)
#     f.set_scales(b.domain.dealias)
#     f['g'] = 3*x**4 + 2*y*x
#     grad = lambda A: operators.Gradient(A, c)
#     div = lambda A: operators.Divergence(A)
#     S = div(grad(f)).evaluate()
#     Sg = 36*x**2
#     assert np.allclose(S['g'], Sg)


# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_divergence_radial_vector(Ntheta, dealias, basis, dtype):
#     Nphi = 1
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype=dtype)
#     f = field.Field(dist=d, bases=(b,), dtype=dtype)
#     f.set_scales(b.domain.dealias)
#     f['g'] = r**2
#     grad = lambda A: operators.Gradient(A, c)
#     div = lambda A: operators.Divergence(A)
#     h = div(grad(f)).evaluate()
#     hg = 4
#     assert np.allclose(h['g'], hg)


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_divergence_tensor(Nphi, Ntheta, dealias, basis, dtype):
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype)
#     v = field.Field(dist=d, tensorsig=(c,), bases=(b,), dtype=dtype)
#     v.set_scales(b.domain.dealias)
#     ex = np.array([-np.sin(phi)+0.*r,np.cos(phi)+0.*r])
#     ey = np.array([np.cos(phi)+0.*r,np.sin(phi)+0.*r])
#     v['g'] = 4*x**3*ey + 3*y**2*ey
#     grad = lambda A: operators.Gradient(A, c)
#     div = lambda A: operators.Divergence(A)
#     U = div(grad(v)).evaluate()
#     Ug = (24*x + 6)*ey
#     assert np.allclose(U['g'], Ug)


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_curl_vector(Nphi, Ntheta, dealias, basis, dtype):
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype)
#     v = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     v.set_scales(b.domain.dealias)
#     ex = np.array([-np.sin(phi)+0.*r,np.cos(phi)+0.*r])
#     ey = np.array([np.cos(phi)+0.*r,np.sin(phi)+0.*r])
#     v['g'] = 4*x**3*ey + 3*y**2*ey
#     u = operators.Curl(v).evaluate()
#     ug = 12*x**2
#     assert np.allclose(u['g'], ug)
@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('dtype', [np.complex128])
def test_laplacian_scalar(Nphi,  Ntheta, dealias, dtype):
    #c, d, b, phi, theta, x, y = build_sphere(Nphi, Ntheta, dealias, dtype)
    c, d, b, phi, theta = build_sphere(Nphi, Ntheta, dealias, dtype)
    u = field.Field(dist=d, bases=(b,), dtype=dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    u.set_scales(b.domain.dealias)
    m = 10
    l = 10
    f['g'] = sph_harm(m,l,phi,theta)

    u = operators.Laplacian(f,c).evaluate()
    assert np.allclose(u['g'], -f['g']*(l*(l+1)))

@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('dtype', [np.complex128])
def test_implicit_laplacian_scalar(Nphi,  Ntheta, dealias, dtype):
    #c, d, b, phi, theta, x, y = build_sphere(Nphi, Ntheta, dealias, dtype)
    c, d, b, phi, theta = build_sphere(Nphi, Ntheta, dealias, dtype)
    u = field.Field(dist=d, bases=(b,), dtype=dtype)
    f = field.Field(dist=d, bases=(b,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    u.set_scales(b.domain.dealias)
    m = 10
    l = 10
    f['g'] = sph_harm(m,l,phi,theta)

    lap = lambda A: operators.Laplacian(A,c)
    problem = problems.LBVP([u])
    problem.add_equation((lap(u),f), condition='ntheta != 0')
    problem.add_equation((u,0), condition='ntheta ==0')
    solver = solvers.LinearBoundaryValueSolver(problem)
    solver.solve()
    assert np.allclose(u['g'], -f['g']/(l*(l+1)))

@pytest.mark.parametrize('Nphi', Nphi_range)
@pytest.mark.parametrize('Ntheta', Ntheta_range)
@pytest.mark.parametrize('dealias', dealias_range)
@pytest.mark.parametrize('dtype', [np.complex128])
def test_implicit_laplacian_vector(Nphi,  Ntheta, dealias, dtype):
    #c, d, b, phi, theta, x, y = build_sphere(Nphi, Ntheta, dealias, dtype)
    c, d, b, phi, theta = build_sphere(Nphi, Ntheta, dealias, dtype)
    u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    f = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
    f.set_scales(b.domain.dealias)
    u.set_scales(b.domain.dealias)
    m0 = 1
    l0 = 1
    m1 = 1
    l1 = 2
    f['g'][0] = sph_harm(m0,l0,phi,theta)
    f['g'][1] = sph_harm(m1,l1,phi,theta)
    lap = lambda A: operators.Laplacian(A,c)
    problem = problems.LBVP([u])
    problem.add_equation((lap(u),f))
    solver = solvers.LinearBoundaryValueSolver(problem)
    solver.solve()

    ug = [np.exp(1j*phi)*np.sqrt(3/(2*np.pi))*(1+2j*np.sqrt(5)*np.tan(theta)**(-2) + np.sin(theta)**-2)*np.sin(theta)/2,
          -np.exp(1j*phi)*np.sqrt(3/(2*np.pi))*(4j - 7*np.sqrt(5) + 5*np.sqrt(5)*np.cos(2*theta))/(4*np.tan(theta))]
    assert np.allclose(u['g'], ug)


# @pytest.mark.parametrize('Nphi', Nphi_range)
# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_laplacian_vector(Nphi,  Ntheta, dealias, basis, dtype):
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype)
#     v = field.Field(dist=d, tensorsig=(c,), bases=(b,), dtype=dtype)
#     v.set_scales(b.domain.dealias)
#     ex = np.array([-np.sin(phi)+0.*r,np.cos(phi)+0.*r])
#     ey = np.array([np.cos(phi)+0.*r,np.sin(phi)+0.*r])
#     v['g'] = 4*x**3*ey + 3*y**2*ey
#     U = operators.Laplacian(v,c).evaluate()
#     Ug = (24*x + 6)*ey
#     assert np.allclose(U['g'], Ug)


# @pytest.mark.parametrize('Ntheta', Ntheta_range)
# @pytest.mark.parametrize('dealias', dealias_range)
# @pytest.mark.parametrize('basis', [build_disk, build_annulus])
# @pytest.mark.parametrize('dtype', [np.float64, np.complex128])
# def test_laplacian_radial_vector(Ntheta, dealias, basis, dtype):
#     Nphi = 1
#     c, d, b, phi, r, x, y = basis(Nphi, Ntheta, dealias, dtype=dtype)
#     u = field.Field(dist=d, bases=(b,), tensorsig=(c,), dtype=dtype)
#     u.set_scales(b.domain.dealias)
#     u['g'][1] = 4 * r**3
#     v = operators.Laplacian(u, c).evaluate()
#     vg = 0 * v['g']
#     vg[1] = 32 * r
#     assert np.allclose(v['g'], vg)

