from numpy import floor, roll, array, zeros, exp, pi, sin, ndarray

def Nstop(x,m): 
    """
    Return the number of terms to keep in partial wave expansion
    according to Wiscombe (1980) and Yang (2003)
    """

    ### Wiscombe (1980)
    xl = x[-1]
    if xl < 8.:
        ns = floor(xl + 4. * xl**(1./3.) + 1.)
    elif xl < 4200.:
        ns = floor(xl + 4.05 * xl**(1./3.) + 2.)
    elif xl > 4199.:
        ns = floor(xl + 4. * xl**(1./3.) + 2.)

    ### Yang (2003) Eq. (30)
    ns = [ns]
    ns.extend(map(abs,x*m))
    ns.extend(map(abs,roll(x,-1)*m))
    return int(floor(max(ns))+15)

def sphere_coefficients(ap,np,nm,lamb,resolution=0):
    """
    Calculate the Mie scattering coefficients for a multilayered sphere 
    illuminated by a coherent plane wave linearly polarized in the x direction.
    
    Args:
        ap: [nlayers] radii of layered sphere [micrometers]
            NOTE: ap and np are reordered automatically so that
            ap is in ascending order.
        np: [nlayers] (complex) refractive indexes of sphere's layers
        nm: (complex) refractive index of medium
        lamb: wavelength of light [micrometers]

    Keywrods:
        resolution: minimum magnitude of Lorenz-Mie coefficients to retain.
              Default: See references
    Returns:
        ab: the coefficients a,b
    """

    if type(ap) != ndarray:
        ap = [ap,ap]
        np = [np,np]
    ap = array(ap)
    np = array(np)

    nlayers = ap.ndim

    if np.ndim != nlayers:
        print "Error Warning: ap and np must have the same number of elements"

    # arrange shells in size order
    if nlayers > 1: 
        order = ap.argsort()
        ap = ap[order]
        np = np[order]

    x = map(abs,(2.0 * pi * nm * ap / lamb)) # size parameter [array]
    m = np/nm                                # relative refractive index [array]
    nmax = Nstop(x, m)            # number of terms in partial-wave expansion
    ci = complex(0,1.)            # imaginary unit


    # arrays for storing results
    ab = zeros([nmax+1, 2],complex)  ##Note:  May be faster not to use zeros
    D1     = zeros(nmax+2,complex)
    D1_a   = zeros([nmax+2, nlayers],complex)
    D1_am1 = zeros([nmax+2, nlayers],complex)

    D3     = zeros(nmax+1,complex)
    D3_a   = zeros([nmax+1, nlayers],complex)
    D3_am1 = zeros([nmax+1, nlayers],complex)

    Psi         = zeros(nmax+1,complex) 
    Zeta        = zeros(nmax+1,complex) 
    PsiZeta     = zeros(nmax+1,complex) 
    PsiZeta_a   = zeros([nmax+1, nlayers],complex) 
    PsiZeta_am1 = zeros([nmax+1, nlayers],complex) 

    Q  = zeros([nmax+1, nlayers],complex) 
    Ha = zeros([nmax+1, nlayers],complex) 
    Hb = zeros([nmax+1, nlayers],complex) 

    # Calculate D1, D3 and PsiZeta for Z1 in the first layer
    z1 = x[0] * m[0]

    # D1_a[0, nmax + 1] = dcomplex(0) # Eq. (16a)
    for n in xrange(nmax+1, 0, -1):     # downward recurrence Eq. (16b)
        D1_a[n-1,0] = n/z1 - 1.0/(D1_a[n,0] + n/z1)

    PsiZeta_a[0, 0] = 0.5 * (1. - exp(2. * ci * z1)) # Eq. (18a)
    D3_a[0, 0] = ci                                  # Eq. (18a)
    for n in xrange(1, nmax+1):          #upward recurrence Eq. (18b)
        PsiZeta_a[n,0] = PsiZeta_a[n-1,0] * (n/z1 - D1_a[n-1,0]) * (n/z1 - D3_a[n-1,0])
        D3_a[n, 0] = D1_a[n, 0] + ci/PsiZeta_a[n, 0]

# Ha and Hb in the core
    Ha[:, 0] = D1_a[0:-1, 0]     # Eq. (7a)
    Hb[:, 0] = D1_a[0:-1, 0]     # Eq. (8a)

# Iterate from layer 2 to layer L
    for ii in xrange(1, nlayers): 
        z1 = x[ii] * m[ii]
        z2 = x[ii-1] * m[ii]
        # Downward recurrence for D1, Eqs. (16a) and (16b)
        #   D1_a[ii, nmax+1]   = dcomplex(0)      # Eq. (16a)
        #   D1_am1[ii, nmax+1] = dcomplex(0)
        for n in xrange(nmax+1, 0, -1):# Eq. (16 b)
            D1_a[n-1, ii]   = n/z1 - 1./(D1_a[n, ii]   + n/z1)
            D1_am1[n-1, ii] = n/z2 - 1./(D1_am1[n, ii] + n/z2)
            
       # Upward recurrence for PsiZeta and D3, Eqs. (18a) and (18b)
        PsiZeta_a[0, ii]   = 0.5 * (1. - exp(2. * ci * z1)) # Eq. (18a)
        PsiZeta_am1[0, ii] = 0.5 * (1. - exp(2. * ci * z2))
        D3_a[0, ii]   = ci           
        D3_am1[0, ii] = ci           
        for n in xrange(1, nmax+1):    # Eq. (18b)
            PsiZeta_a[n, ii]   = PsiZeta_a[n-1, ii] * (n/z1 -  D1_a[n-1, ii]) * (n/z1 -  D3_a[n-1, ii])
            PsiZeta_am1[n, ii] = PsiZeta_am1[n-1, ii] * (n/z2 - D1_am1[n-1, ii]) * (n/z2 - D3_am1[n-1, ii])
            D3_a[n, ii]   = D1_a[n, ii]   + ci/PsiZeta_a[n, ii]
            D3_am1[n, ii] = D1_am1[n, ii] + ci/PsiZeta_am1[n, ii]


   # Upward recurrence for Q
        Q[0,ii] = (exp(-2. * ci * z2) - 1.) / (exp(-2. * ci * z1) - 1.)
        for n in xrange(1, nmax+1):
            Num = (z1 * D1_a[n, ii]   + n) * (n - z1 * D3_a[n-1, ii])
            Den = (z2 * D1_am1[n, ii] + n) * (n - z2 * D3_am1[n-1, ii])
            Q[n, ii] = (x[ii-1]/x[ii])**2 * Q[n-1, ii] * Num/Den

   # Upward recurrence for Ha and Hb, Eqs. (7b), (8b) and (12) - (15)
        for n in xrange(1, nmax+1):
            G1 = m[ii] * Ha[n, ii-1] - m[ii-1] * D1_am1[n, ii]
            G2 = m[ii] * Ha[n, ii-1] - m[ii-1] * D3_am1[n, ii]
            Temp = Q[n, ii] * G1
            Num = G2 * D1_a[n, ii] - Temp * D3_a[n, ii]
            Den = G2 - Temp
            Ha[n, ii] = Num/Den
            
            G1 = m[ii-1] * Hb[n, ii-1] - m[ii] * D1_am1[n, ii]
            G2 = m[ii-1] * Hb[n, ii-1] - m[ii] * D3_am1[n, ii]
            Temp = Q[n, ii] * G1
            Num = G2 * D1_a[n, ii] - Temp * D3_a[n, ii]
            Den = G2 - Temp
            Hb[n, ii] = Num/Den

       #ii (layers)
       
    z1 = complex(x[-1])
    # Downward recurrence for D1, Eqs. (16a) and (16b)
    # D1[nmax+1] = dcomplex(0)            # Eq. (16a)
    for n in xrange(nmax, 0, -1):         # Eq. (16b)
        D1[n-1] = n/z1 - (1./(D1[n] + n/z1))

# Upward recurrence for Psi, Zeta, PsiZeta and D3, Eqs. (18a) and (18b)
    Psi[0]     =  sin(z1)                 # Eq. (18a)
    Zeta[0]    = -ci * exp(ci * z1)
    PsiZeta[0] =  0.5 * (1. - exp(2. * ci * z1))
    D3[0]      = ci
    for n in xrange(1, nmax+1):           # Eq. (18b)
        Psi[n]  = Psi[n-1]  * (n/z1 - D1[n-1])
        Zeta[n] = Zeta[n-1] * (n/z1 - D3[n-1])
        PsiZeta[n] = PsiZeta[n-1] * (n/z1 -D1[n-1]) * (n/z1 - D3[n-1])
        D3[n] = D1[n] + ci/PsiZeta[n]

# Scattering coefficients, Eqs. (5) and (6)
    n = map(float,range(nmax + 1))
    ab[:, 0]  = (Ha[:, -1]/m[-1] + n/x[-1]) * Psi  - roll(Psi,  1) # Eq. (5)
    ab[:, 0] /= (Ha[:, -1]/m[-1] + n/x[-1]) * Zeta - roll(Zeta, 1)
    ab[:, 1]  = (Hb[:, -1]*m[-1] + n/x[-1]) * Psi  - roll(Psi,  1) # Eq. (6)
    ab[:, 1] /= (Hb[:, -1]*m[-1] + n/x[-1]) * Zeta - roll(Zeta, 1)
    ab[0, :]  = complex(0.,0.)
    if (resolution > 0):
        w = abs(ab).sum(axis=1)
        ab = ab[(w>resolution),:]
    
    return ab

