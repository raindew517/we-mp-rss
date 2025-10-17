import http from './http'

export const exportArticles = (params:any) => {
    const requestData = {
      mp_id: params.mp_id,
      doc_id: params.scope === 'selected' ? params.ids : [],
      page_size: params.limit||10,
      page_count: params.page_count || 1,
      add_title: true,
      remove_images: true,
      remove_links: false,
      export_md: params.format.includes('md'),
      export_docx: params.format.includes('docx'),
      export_json: params.format.includes('json'),
      export_csv: params.format.includes('csv'),
      export_pdf: params.format.includes('pdf'),
      zip_filename: ''
    };
  return http.post<{code: number, data: string}>('/wx/tools/export/articles', requestData, {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
}