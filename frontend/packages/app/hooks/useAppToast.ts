import { useToastController } from '@my/ui'

export function useAppToast() {
  const toast = useToastController()

  const showToast = (title: string, options?: { message?: string; type?: 'success' | 'error' }) => {
    toast.show(title, {
      message: options?.message,
      // Aquí podrías añadir lógica para cambiar el color del toast según el tipo
    })
  }

  return showToast
}
