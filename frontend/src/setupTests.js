import '@testing-library/jest-dom'

// jsdom does not implement URL.createObjectURL/revokeObjectURL;
// define them so vi.spyOn can spy on them in tests.
if (!window.URL.createObjectURL) {
  window.URL.createObjectURL = () => 'blob:mock'
}
if (!window.URL.revokeObjectURL) {
  window.URL.revokeObjectURL = () => {}
}
