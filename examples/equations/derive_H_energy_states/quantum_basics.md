# Derivations from the Schrödinger Equation in Quantum Mechanics 

## 1. Time-dependent Schrödinger Equation

The fundamental postulate of non-relativistic quantum mechanics states that the evolution of a quantum state $\Psi(\vec{r}, t)$ is governed by the time-dependent Schrödinger equation:

$$
i \hbar \frac{\partial}{\partial t} \Psi(\vec{r}, t)=\hat{H} \Psi(\vec{r}, t)
$$

Here, $\hat{H}$ is the Hamiltonian operator representing the total energy of the system.

## 2. Hamiltonian Operator

For a single particle of mass $m$ in a potential $V(\vec{r})$, the Hamiltonian is:

$$
\hat{H}=-\frac{\hbar^{2}}{2 m} \nabla^{2}+V(\vec{r})
$$

Substituting Eq. 2 into Eq. 1, we obtain the explicit form of the time-dependent Schrödinger equation:

$$
i \hbar \frac{\partial}{\partial t} \Psi(\vec{r}, t)=\left(-\frac{\hbar^{2}}{2 m} \nabla^{2}+V(\vec{r})\right) \Psi(\vec{r}, t)
$$

## 3. Separation of Variables

To solve Eq. 3, we assume a separable solution of the form:

$$
\Psi(\vec{r}, t)=\psi(\vec{r}) T(t)
$$

Substituting Eq. 4 into Eq. 3, we obtain:

$$
i \hbar \psi(\vec{r}) \frac{d T(t)}{d t}=\left(-\frac{\hbar^{2}}{2 m} \nabla^{2} \psi(\vec{r})+V(\vec{r}) \psi(\vec{r})\right) T(t)
$$

Dividing both sides by $\psi(\vec{r}) T(t)$, we get:

$$
\frac{i \hbar}{T(t)} \frac{d T(t)}{d t}=\frac{1}{\psi(\vec{r})}\left(-\frac{\hbar^{2}}{2 m} \nabla^{2} \psi(\vec{r})+V(\vec{r}) \psi(\vec{r})\right)
$$

Since the left-hand side depends only on $t$ and the right-hand side only on $\vec{r}$, both sides must equal a constant $E$, which we interpret as the energy of the system.# 4. Time-independent Schrödinger Equation 

From the separation in Eq. 6, we obtain two equations. The first is the time evolution equation:

$$
i \hbar \frac{d T(t)}{d t}=E T(t)
$$

The second is the time-independent Schrödinger equation:

$$
-\frac{\hbar^{2}}{2 m} \nabla^{2} \psi(\vec{r})+V(\vec{r}) \psi(\vec{r})=E \psi(\vec{r})
$$

## 5. Free Particle Solution

Let us now consider the special case of a free particle where $V(\vec{r})=0$. Substituting into Eq. 8:

$$
-\frac{\hbar^{2}}{2 m} \nabla^{2} \psi(\vec{r})=E \psi(\vec{r})
$$

This is a Helmholtz equation, and its general solution is a plane wave:

$$
\psi(\vec{r})=A e^{i \vec{k} \cdot \vec{r}}, \quad E=\frac{\hbar^{2} k^{2}}{2 m}
$$

## 6. Particle in a 1D Infinite Potential Well

Consider a particle in a 1D box of length $L$ with infinite potential walls. The potential is:

$$
V(x)= \begin{cases}0, & 0<x<L \\ \infty, & \text { otherwise }\end{cases}
$$

Inside the well, the time-independent Schrödinger equation (Eq. 8) simplifies to:

$$
-\frac{\hbar^{2}}{2 m} \frac{d^{2} \psi(x)}{d x^{2}}=E \psi(x)
$$

Solving this second-order differential equation with boundary conditions $\psi(0)=\psi(L)=0$ gives:

$$
\psi_{n}(x)=\sqrt{\frac{2}{L}} \sin \left(\frac{n \pi x}{L}\right), \quad E_{n}=\frac{n^{2} \pi^{2} \hbar^{2}}{2 m L^{2}}
$$

## 7. Harmonic Oscillator

Next, we consider the harmonic oscillator potential:

$$
V(x)=\frac{1}{2} m \omega^{2} x^{2}
$$

Plugging this into the time-independent Schrödinger equation (Eq. 8):

$$
-\frac{\hbar^{2}}{2 m} \frac{d^{2} \psi(x)}{d x^{2}}+\frac{1}{2} m \omega^{2} x^{2} \psi(x)=E \psi(x)
$$The solution involves Hermite polynomials $H_{n}(x)$ :

$$
\psi_{n}(x)=N_{n} e^{-\frac{m \omega_{r} x^{2}}{2 \hbar}} H_{n}\left(\sqrt{\frac{m \omega}{\hbar}} x\right)
$$

With quantized energy levels:

$$
E_{n}=\hbar \omega\left(n+\frac{1}{2}\right)
$$

# 8. Hydrogen Atom (Radial Part) 

For the hydrogen atom, we consider a central Coulomb potential:

$$
V(r)=-\frac{e^{2}}{4 \pi \epsilon_{0} r}
$$

The radial part of the time-independent Schrödinger equation (from Eq. 8 in spherical coordinates) becomes:

$$
-\frac{\hbar^{2}}{2 \mu}\left[\frac{d^{2}}{d r^{2}}+\frac{2}{r} \frac{d}{d r}-\frac{l(l+1)}{r^{2}}\right] R(r)-\frac{e^{2}}{4 \pi \epsilon_{0} r} R(r)=E R(r)
$$

Solving this equation yields quantized energy levels:

$$
E_{n}=-\frac{\mu e^{4}}{2\left(4 \pi \epsilon_{0}\right)^{2} \hbar^{2} n^{2}}, \quad n=1,2,3, \ldots
$$

## 9. Commutator of Position and Momentum

A fundamental result in quantum mechanics is the commutator between position and momentum operators:

$$
\left[\hat{x}, \hat{p}_{x}\right]=i \hbar
$$

This forms the foundation for the uncertainty principle.

## 10. Heisenberg Uncertainty Principle

Using the canonical commutation relation in Eq. 21, we obtain the Heisenberg uncertainty principle:

$$
\Delta x \Delta p \geq \frac{\hbar}{2}
$$

This inequality encapsulates the intrinsic limit on the precision of simultaneous measurements of position and momentum.