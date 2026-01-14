require("dotenv").config({ path: require("path").resolve(process.cwd(), ".env.local") })

module.exports = {
  datasource: {
    url: process.env.DATABASE_URL_MIGRATIONS || process.env.DATABASE_URL,
  },
}
