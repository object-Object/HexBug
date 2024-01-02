module.exports = {
    apps: [{
        name: "HexBug",
        script: "./scripts/pm2/run.sh",
        min_uptime: "5s",
        max_restarts: 5,
    }]
}
