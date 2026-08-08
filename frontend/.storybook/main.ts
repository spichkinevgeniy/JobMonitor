import type { StorybookConfig } from '@storybook/react-vite'
import { mergeConfig } from 'vite'

const sourceRoot = new URL('../apps/shell/src', import.meta.url).pathname

const config: StorybookConfig = {
  stories: ['../apps/shell/src/**/*.stories.@(ts|tsx)'],
  framework: '@storybook/react-vite',
  viteFinal: async (config) =>
    mergeConfig(config, {
      resolve: {
        alias: {
          '@': sourceRoot,
        },
      },
    }),
}

export default config
