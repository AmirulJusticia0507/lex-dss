import Swal from 'sweetalert2'

const brandClasses = {
  popup: 'lex-swal-popup',
  title: 'lex-swal-title',
  confirmButton: 'lex-swal-confirm',
  cancelButton: 'lex-swal-cancel',
}

export function showToast(icon, title) {
  return Swal.fire({
    toast: true,
    position: 'top-end',
    icon,
    title,
    showConfirmButton: false,
    timer: 2800,
    timerProgressBar: true,
    customClass: { popup: 'lex-swal-toast' },
  })
}

export function confirmAction({ title, text, confirmText = 'Ya, lanjutkan', icon = 'warning' }) {
  return Swal.fire({
    title,
    text,
    icon,
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: 'Batal',
    reverseButtons: true,
    buttonsStyling: false,
    customClass: brandClasses,
  })
}
