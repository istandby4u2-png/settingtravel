/** 공개 사이트(istandby4u2) 링크·문구. SNS URL은 실제 계정 주소로 바꿔 주세요. */
export const SITE_CONFIG = {
  title: "SETTING TRAVEL",
  tagline: "책・영화・드라마 속 그 곳",
  legacySitesUrl: "https://sites.google.com/site/istandby4u2",
  brunch: "https://brunch.co.kr/@istandby4u2",
  naverBlog: "https://blog.naver.com/istandby4u2",
  books: [
    {
      label: "다정한 여행의 배경",
      href: "https://search.shopping.naver.com/book/catalog/32503506784",
      coverSrc: "/books/dajeong-yeohaeng.png",
    },
    {
      label: "리얼 홋카이도",
      href: "https://search.shopping.naver.com/book/catalog/54911461237",
      coverSrc: "/books/real-hokkaido.png",
    },
  ],
  social: {
    instagram: "https://www.instagram.com/moonee_lee/",
    youtube: "https://www.youtube.com/channel/UC_GEes8puaUEHUYy053v64Q",
  },
  copyright: "istandby4u2",
} as const;
