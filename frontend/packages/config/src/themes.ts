import { tokens } from '@tamagui/themes'

const light = {
  background: '#fff',
  backgroundHover: tokens.color.gray3Light,
  backgroundPress: tokens.color.gray4Light,
  backgroundFocus: tokens.color.gray5Light,
  borderColor: tokens.color.gray4Light,
  borderColorHover: tokens.color.gray6Light,
  color: tokens.color.gray12Light,
  colorHover: tokens.color.gray11Light,
  colorPress: tokens.color.gray10Light,
  colorFocus: tokens.color.gray6Light,
  shadowColor: tokens.color.grayA5Light,
  shadowColorHover: tokens.color.grayA6Light,
}

type BaseTheme = typeof light

const dark: BaseTheme = {
  background: '#111',
  backgroundHover: tokens.color.gray3Dark,
  backgroundPress: tokens.color.gray4Dark,
  backgroundFocus: tokens.color.gray5Dark,
  borderColor: tokens.color.gray3Dark,
  borderColorHover: tokens.color.gray4Dark,
  color: '#ddd',
  colorHover: tokens.color.gray11Dark,
  colorPress: tokens.color.gray10Dark,
  colorFocus: tokens.color.gray6Dark,
  shadowColor: tokens.color.grayA6Dark,
  shadowColorHover: tokens.color.grayA7Dark,
}

const brand: BaseTheme = {
  ...light,
  background: '#1fa8d8',
  backgroundHover: '#1c97c2',
  backgroundPress: '#1986ac',
  backgroundFocus: '#167596',
  color: '#fff',
  colorHover: '#eee',
  colorPress: '#ddd',
  colorFocus: '#ccc',
  borderColor: '#1fa8d8',
  borderColorHover: '#1c97c2',
}

export const themes = {
  light,
  dark,
  brand,
} satisfies { [key: string]: BaseTheme }
