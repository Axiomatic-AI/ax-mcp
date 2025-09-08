def calculate_transmission(rf_cutoff_frequency_hz, f_3dB, insertion_loss_DC, roll_off_factor, parasitic_loss_factor):
    """
    Calculate RF transmission characteristics of the optical engine package.
    """
    import numpy as np

    # Convert frequency to GHz
    f_GHz = rf_cutoff_frequency_hz / 1e9
    f_3dB_GHz = f_3dB / 1e9

    # Low-pass filter response
    f_ratio = f_GHz / f_3dB_GHz
    H_squared = 1.0 / (1.0 + np.power(f_ratio, 2.0 * roll_off_factor))

    # Convert to dB
    H_dB = 10.0 * np.log10(H_squared)

    # Add DC insertion loss
    H_dB = H_dB + insertion_loss_DC

    # Add frequency-dependent parasitic losses
    parasitic_dB = -parasitic_loss_factor * np.sqrt(f_GHz)

    transmission_dB = H_dB + parasitic_dB

    return transmission_dB
