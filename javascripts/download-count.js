document$.subscribe(() => {
  const counter = document.querySelector(".download-count")
  if (!counter) return

  fetch("https://api.github.com/repos/kacper-jar/HLPatcher/releases?per_page=100")
    .then(response => response.ok ? response.json() : Promise.reject(response.status))
    .then(releases => {
      const total = releases
        .flatMap(release => release.assets)
        .reduce((sum, asset) => sum + asset.download_count, 0)
      counter.textContent = `${total.toLocaleString("en")} downloads`
    })
    .catch(() => {})
})
