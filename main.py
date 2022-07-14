import discord
from lock import *

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

global guilds_id
global roles_id
global nb_guilds
global roles_per_guild
global colors

guilds_id = []
roles_id = [[],[]]
roles_per_guild = []

@client.event
async def on_ready():
  print('{0.user} is logged in.'.format(client))
  db = open(r"db.txt","r")
  bdd = db.read().split('\n')
  db.close()
  bdd.pop()
  bdd = [int(i) for i in bdd]

  global roles_id
  global nb_guilds
  global guilds_id
  global roles_per_guild
  global reactions_per_role

  nb_guilds = bdd[0]
  
  for i in range (nb_guilds):
    roles_per_guild.append( bdd[1 + i*2 + sum(roles_per_guild[0:i])] )
    guilds_id.append(bdd[(i+1)*2+sum(roles_per_guild[0:i])])
    first = True
    for j in range(roles_per_guild[i]):
        if(i>0 and first):
          first = False
          roles_id.append([])
        roles_id[i].append(bdd[(i+1)*2+sum(roles_per_guild[0:i])+j+1])
  
   
@client.event
async def on_guild_join(guild):
  global nb_guilds
  global guilds_id
  global roles_per_guild

  db = open(r"db.txt","r")
  bdd = db.read().split('\n')
  db.close()
  bdd.pop()
  bdd = [int(i) for i in bdd]
  bdd[0] = bdd[0] + 1
  bdd.append(0)
  bdd.append(guild.id)

  nb_guilds = nb_guilds + 1
  guilds_id.append(guild.id)
  roles_per_guild.append(0)

  db_new = open(r"db.txt","w+")
  for b in bdd:
    db_new.write(str(b) + '\n')
  db_new.close()


@client.event
async def on_raw_reaction_add(payload):

  if payload.member == client.user:
    return

  if payload.guild_id not in guilds_id:
    print('guild not found in guilds database')
    return
  
  guild_index = guilds_id.index(payload.guild_id)
  if payload.message_id not in roles_id[guild_index]:
    print('message id not found in database')
    return

  guild = client.get_guild(payload.guild_id)
  channel = discord.utils.get(guild.channels, id = payload.channel_id)
  message = await channel.fetch_message(payload.message_id)
  member = payload.member

  nb = 0
  for r in message.reactions:
    users = await r.users().flatten()
    if member in users:
      nb = nb + 1
      if nb > 1:
        await message.remove_reaction(payload.emoji, member)
        return


  role = discord.utils.get(guild.roles, name = message.content)
  if role is not None:
    await member.add_roles(role, reason="User added reaction")
    print('role added')
  else:
    print('role not found')


@client.event
async def on_raw_reaction_remove(payload):

  if payload.user_id == client.user.id:
    print("bot removed reaction")
    return

  guild_index = guilds_id.index(payload.guild_id)

  if payload.guild_id not in guilds_id or payload.message_id not in roles_id[guild_index]:
    print('guild not found')
    return
  
  guild_index = guilds_id.index(payload.guild_id)
  if payload.message_id not in roles_id[guild_index]:
    print('msg id not found')
    return

  guild = client.get_guild(payload.guild_id)
  channel = discord.utils.get(guild.channels, id = payload.channel_id)
  message = await channel.fetch_message(payload.message_id)
  member = discord.utils.get(guild.members, id = payload.user_id)
  
  for r in message.reactions:
    users = await r.users().flatten()
    if member in users:
      return

  role = discord.utils.get(guild.roles, name = message.content)
  if role is not None:
    await member.remove_roles(role, reason="User removed reaction")
  else:
    print('role not found')


@client.event
async def on_message(message):
  if client.user.mentioned_in(message):
    if message.author == client.user or message.author.bot:
      return
    admin = discord.utils.get(message.guild.roles, name="Admin")
    if admin in message.author.roles:
      message_text = message.content.split()

      if message_text[0] == "<@"+str(client.user.id)+">" or message_text[0] == "<@!"+str(client.user.id)+">":
        if len(message_text) == 1:
          await help(message.channel)
          return
        if message_text[1] == "create" and len(message_text) >= 4:
          c = discord.utils.get(message.guild.channels, name = message_text[2])
          if c is None:
            await message.channel.send("Sorry, this channel does not exist!")
          roles = " ".join(message_text[3:])
          roles = roles.split('|')
          await create_roles(message.guild, c, roles)
        elif message_text[1] == "send" and len(message_text) >= 3:
          c = discord.utils.get(message.guild.channels, name = message_text[2])
          if c is None:
            await message.channel.send("Sorry, this channel does not exist!")
            return
          await send_msg(c, " ".join(message_text[3:]))
        elif message_text[1] == "send_guild" and len(message_text) >= 5:
          g = client.get_guild(int(message_text[2]))
          c = discord.utils.get(g.channels, name = message_text[3])
          if c is None:
            await message.channel.send("Sorry, this channel does not exist!")
            return
          msg = await c.fetch_message(message_text[4])
          await c.send(" ".join(message_text[5:]), reference = msg)
        elif message_text[1] == "delete" and len(message_text) >= 4:
          c = discord.utils.get(message.guild.channels, name = message_text[2])
          if c is None:
            await message.channel.send("Sorry, this channel does not exist!")
          await delete_roles(message.guild, c, message_text[3:])
        elif message_text[1] == "colour" and len(message_text) >= 4:
          role = discord.utils.get(message.guild.roles, name = " ".join(message_text[2:len(message_text)-1]))
          if role is None:
            await message.channel.send("Sorry, role not found!")
            return
          colour = message_text[len(message_text)-1].split('|')
          if len(colour) != 3:
            await message.channel.send("Please provide an RGB code: 255|200|120")
            return
          for i in colour:
            if not i.isnumeric():
              await message.channel.send("Please provide an RGB code: 255|200|120")
              return
          await change_colour(role, colour)
        #else:
         # await help(message.channel)
      #else:
        #await help(message.channel)
    #else:
     # await message.channel.send("Hello Dear, is everything Okay =D ?")

@client.event
async def create_roles(guild, channel, names):
  global roles_id
  global nb_guilds
  global guilds_id
  global roles_per_guild
  global reactions_per_role
  clone = discord.utils.get(guild.roles, name="clone")
  db = open(r"db.txt","r")
  bdd = db.read().split('\n')
  db.close()
  bdd.pop()
  bdd = [int(i) for i in bdd]
  
  guild_index = bdd.index(guild.id)
  guild_index_2 = guilds_id.index(guild.id)
  nbroles_index = guild_index - 1

  bdd[nbroles_index] = bdd[nbroles_index] + len(names)
  roles_per_guild[guild_index_2] = roles_per_guild[guild_index_2] + len(names)
  

  i = 0

  roles = []
  for n in names:
    await guild.create_role(name = n, permissions = clone.permissions, colour = discord.Colour.magenta())
    msg = await channel.send(n)
    await msg.add_reaction('👊')
    bdd.insert(guild_index + i + 1, msg.id)
    roles.append(msg.id)
    i = i + 1 

  if len(roles_id) <= guild_index_2:
    roles_id.append(roles)
  else:
    for j in range(i):
      roles_id[guild_index_2].append(roles[j])

  new_db = open(r"db.txt","w+")
  for line in bdd:
    new_db.write(str(line)+'\n')
  new_db.close()

@client.event
async def delete_roles(guild, channel, msg_ids):
  db = open(r"db.txt","r")
  bdd = db.read().split('\n')
  db.close()
  bdd.pop()
  bdd = [int(i) for i in bdd]

  guild_index = bdd.index(guild.id)
  bdd[guild_index - 1] = bdd[guild_index - 1] - len(msg_ids)
  guild_index_2 = guilds_id.index(guild.id)
  roles_per_guild[guild_index_2] = roles_per_guild[guild_index_2] - len(msg_ids)

  for m in msg_ids:
    if not m.isnumeric():
      await help(channel)
      return

  msg_ids = [int(i) for i in msg_ids]

  for m_id in msg_ids:
    msg = await channel.fetch_message(m_id)
    if msg is None:
      return
    role_name = msg.content
    role = discord.utils.get(guild.roles, name = role_name)
    await role.delete()
    bdd.remove(m_id)
    roles_id[guild_index_2].remove(m_id)
    await msg.delete()

  db_new = open(r"db.txt","w+")
  for b in bdd:
    db_new.write(str(b)+'\n')
  db_new.close()
    
@client.event
async def change_colour(role, colour):
  colour = [int(c) for c in colour]
  c = discord.Colour.from_rgb(colour[0],colour[1],colour[2])
  await role.edit(colour = c)

@client.event
async def send_msg(channel, msg):
  await channel.send(msg)

@client.event 
async def help(channel):
  await channel.send("Hey there!\n\n**To Create New Roles:** <@"+str(client.user.id)+"> create [channel-name] [list of role names (separator = '**|**' )]\n*Example:* <@"+str(client.user.id)+"> create general New Role 1 | New Role 2\n\n**To Send A Message In My Name:**<@"+str(client.user.id)+"> send [channel-name] [your-message]\n*Example:* <@"+str(client.user.id)+"> send general Hello World!\n\n**To Delete Roles:**<@"+str(client.user.id)+"> delete [channel-name (where the roles were created)] [message ids of the roles]\n*Example:* <@"+str(client.user.id)+"> delete general 892045515850645584 892045446011293757\n\n**To Change The Colour of An Existing Role:** <@"+str(client.user.id)+"> colour [role-name] [RGB code separated by: '**|**']\n*Example:* <@"+str(client.user.id)+"> colour Role 1 255|100|20\n")

client.run(token)
