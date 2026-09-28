import { ref, onMounted } from 'vue'

export function usePageLoader(delay = 200) {
  const loading = ref(false)
  let timer = null

  function startLoader() {
    loading.value = true
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      loading.value = false
    }, delay)
  }

  function stopLoader() {
    if (timer) clearTimeout(timer)
    timer = null
    loading.value = false
  }

  onMounted(() => {
    startLoader()
  })

  return { loading, startLoader, stopLoader }
}