module.exports = {
    apps: [{
        name: "HexBug",
        script: "./scripts/pm2/run.sh",
        min_uptime: "30s",
        max_restarts: 3,
    }]
}
